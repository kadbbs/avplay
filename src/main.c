#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/channel_layout.h>
#include <libavutil/imgutils.h>
#include <libavutil/samplefmt.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>

typedef struct Decoder {
    AVFormatContext *fmt;
    AVCodecContext *dec;
    int stream_index;
} Decoder;

static int fail(const char *message, int err)
{
    char buf[AV_ERROR_MAX_STRING_SIZE] = {0};
    if (err < 0) {
        av_strerror(err, buf, sizeof(buf));
        fprintf(stderr, "%s: %s\n", message, buf);
    } else {
        fprintf(stderr, "%s\n", message);
    }
    return err < 0 ? err : AVERROR_UNKNOWN;
}

static void usage(const char *argv0)
{
    fprintf(stderr,
            "Usage:\n"
            "  %s info <input>\n"
            "  %s thumbnail <input> <output.ppm> [width]\n"
            "  %s audio-pcm <input> <output.s16le> [seconds]\n",
            argv0, argv0, argv0);
}

static void close_decoder(Decoder *d)
{
    avcodec_free_context(&d->dec);
    avformat_close_input(&d->fmt);
}

static int open_decoder(const char *input, enum AVMediaType type, Decoder *out)
{
    int ret;
    const AVCodec *codec = NULL;

    memset(out, 0, sizeof(*out));
    out->stream_index = -1;

    ret = avformat_open_input(&out->fmt, input, NULL, NULL);
    if (ret < 0) return fail("Could not open input", ret);

    ret = avformat_find_stream_info(out->fmt, NULL);
    if (ret < 0) return fail("Could not read stream info", ret);

    ret = av_find_best_stream(out->fmt, type, -1, -1, &codec, 0);
    if (ret < 0) return fail("Could not find requested stream", ret);
    out->stream_index = ret;

    out->dec = avcodec_alloc_context3(codec);
    if (!out->dec) return AVERROR(ENOMEM);

    ret = avcodec_parameters_to_context(out->dec, out->fmt->streams[out->stream_index]->codecpar);
    if (ret < 0) return fail("Could not copy codec parameters", ret);

    ret = avcodec_open2(out->dec, codec, NULL);
    if (ret < 0) return fail("Could not open decoder", ret);
    return 0;
}

static int command_info(const char *input)
{
    int ret;
    AVFormatContext *fmt = NULL;

    ret = avformat_open_input(&fmt, input, NULL, NULL);
    if (ret < 0) return fail("Could not open input", ret);
    ret = avformat_find_stream_info(fmt, NULL);
    if (ret < 0) {
        avformat_close_input(&fmt);
        return fail("Could not read stream info", ret);
    }

    printf("File: %s\n", input);
    printf("Container: %s\n", fmt->iformat ? fmt->iformat->long_name : "unknown");
    printf("Duration: %.3f seconds\n", fmt->duration == AV_NOPTS_VALUE ? 0.0 : fmt->duration / (double)AV_TIME_BASE);
    printf("Streams: %u\n\n", fmt->nb_streams);

    for (unsigned i = 0; i < fmt->nb_streams; i++) {
        AVCodecParameters *par = fmt->streams[i]->codecpar;
        printf("[%u] type=%s codec=%s", i,
               av_get_media_type_string(par->codec_type),
               avcodec_get_name(par->codec_id));
        if (par->codec_type == AVMEDIA_TYPE_VIDEO) {
            printf(" %dx%d", par->width, par->height);
        } else if (par->codec_type == AVMEDIA_TYPE_AUDIO) {
            printf(" %dHz channels=%d", par->sample_rate, par->ch_layout.nb_channels);
        }
        printf("\n");
    }

    avformat_close_input(&fmt);
    return 0;
}

static int decode_first_frame(Decoder *d, AVFrame *frame)
{
    int ret;
    AVPacket *pkt = av_packet_alloc();
    if (!pkt) return AVERROR(ENOMEM);

    while ((ret = av_read_frame(d->fmt, pkt)) >= 0) {
        if (pkt->stream_index != d->stream_index) {
            av_packet_unref(pkt);
            continue;
        }
        ret = avcodec_send_packet(d->dec, pkt);
        av_packet_unref(pkt);
        if (ret < 0) break;
        ret = avcodec_receive_frame(d->dec, frame);
        if (ret == AVERROR(EAGAIN)) continue;
        av_packet_free(&pkt);
        return ret < 0 ? ret : 1;
    }

    av_packet_free(&pkt);
    return 0;
}

static int command_thumbnail(const char *input, const char *output, int width)
{
    int ret, height;
    Decoder d;
    AVFrame *frame = av_frame_alloc();
    uint8_t *rgb[4] = {0};
    int linesize[4] = {0};
    struct SwsContext *sws = NULL;
    FILE *fp = NULL;

    if (!frame) return AVERROR(ENOMEM);
    ret = open_decoder(input, AVMEDIA_TYPE_VIDEO, &d);
    if (ret < 0) goto done;
    ret = decode_first_frame(&d, frame);
    if (ret <= 0) { ret = fail("No video frame decoded", AVERROR_EOF); goto done; }

    height = (int)((int64_t)frame->height * width / frame->width);
    sws = sws_getContext(frame->width, frame->height, frame->format,
                         width, height, AV_PIX_FMT_RGB24,
                         SWS_BILINEAR, NULL, NULL, NULL);
    if (!sws) { ret = AVERROR(EINVAL); goto done; }
    ret = av_image_alloc(rgb, linesize, width, height, AV_PIX_FMT_RGB24, 1);
    if (ret < 0) goto done;
    sws_scale(sws, (const uint8_t * const *)frame->data, frame->linesize, 0, frame->height, rgb, linesize);

    fp = fopen(output, "wb");
    if (!fp) { ret = AVERROR(errno); goto done; }
    fprintf(fp, "P6\n%d %d\n255\n", width, height);
    for (int y = 0; y < height; y++) fwrite(rgb[0] + y * linesize[0], 1, (size_t)width * 3, fp);
    printf("Wrote thumbnail: %s (%dx%d)\n", output, width, height);
    ret = 0;

done:
    if (fp) fclose(fp);
    if (rgb[0]) av_freep(&rgb[0]);
    sws_freeContext(sws);
    av_frame_free(&frame);
    close_decoder(&d);
    return ret;
}

static int command_audio_pcm(const char *input, const char *output, double seconds)
{
    int ret;
    Decoder d;
    AVPacket *pkt = av_packet_alloc();
    AVFrame *frame = av_frame_alloc();
    SwrContext *swr = NULL;
    AVChannelLayout layout;
    FILE *fp = NULL;
    int64_t written = 0;
    int max_samples = seconds > 0 ? (int)(seconds * 48000) : 0;

    if (!pkt || !frame) return AVERROR(ENOMEM);
    av_channel_layout_default(&layout, 2);
    ret = open_decoder(input, AVMEDIA_TYPE_AUDIO, &d);
    if (ret < 0) goto done;
    fp = fopen(output, "wb");
    if (!fp) { ret = AVERROR(errno); goto done; }

    while ((ret = av_read_frame(d.fmt, pkt)) >= 0) {
        if (pkt->stream_index != d.stream_index) { av_packet_unref(pkt); continue; }
        ret = avcodec_send_packet(d.dec, pkt);
        av_packet_unref(pkt);
        if (ret < 0) break;
        while ((ret = avcodec_receive_frame(d.dec, frame)) >= 0) {
            uint8_t **out = NULL;
            int linesize = 0;
            int samples;
            if (!swr) {
                ret = swr_alloc_set_opts2(&swr, &layout, AV_SAMPLE_FMT_S16, 48000,
                                          &frame->ch_layout, frame->format, frame->sample_rate, 0, NULL);
                if (ret < 0 || (ret = swr_init(swr)) < 0) goto done;
            }
            samples = (int)av_rescale_rnd(swr_get_delay(swr, frame->sample_rate) + frame->nb_samples,
                                          48000, frame->sample_rate, AV_ROUND_UP);
            if (max_samples > 0 && written + samples > max_samples) samples = max_samples - (int)written;
            if (samples <= 0) goto success;
            ret = av_samples_alloc_array_and_samples(&out, &linesize, 2, samples, AV_SAMPLE_FMT_S16, 0);
            if (ret < 0) goto done;
            ret = swr_convert(swr, out, samples, (const uint8_t **)frame->extended_data, frame->nb_samples);
            if (ret > 0) {
                fwrite(out[0], 1, (size_t)ret * 2 * av_get_bytes_per_sample(AV_SAMPLE_FMT_S16), fp);
                written += ret;
            }
            av_freep(&out[0]);
            av_freep(&out);
            av_frame_unref(frame);
            if (max_samples > 0 && written >= max_samples) goto success;
        }
        if (ret != AVERROR(EAGAIN) && ret != AVERROR_EOF) break;
    }

success:
    printf("Wrote audio: %s (%" PRId64 " samples, stereo 48kHz s16le)\n", output, written);
    ret = 0;

done:
    if (fp) fclose(fp);
    swr_free(&swr);
    av_channel_layout_uninit(&layout);
    av_frame_free(&frame);
    av_packet_free(&pkt);
    close_decoder(&d);
    return ret;
}

int main(int argc, char **argv)
{
    if (argc < 3) { usage(argv[0]); return 1; }
    if (strcmp(argv[1], "info") == 0 && argc == 3) return command_info(argv[2]) < 0;
    if (strcmp(argv[1], "thumbnail") == 0 && (argc == 4 || argc == 5)) return command_thumbnail(argv[2], argv[3], argc == 5 ? atoi(argv[4]) : 320) < 0;
    if (strcmp(argv[1], "audio-pcm") == 0 && (argc == 4 || argc == 5)) return command_audio_pcm(argv[2], argv[3], argc == 5 ? atof(argv[4]) : 0.0) < 0;
    usage(argv[0]);
    return 1;
}
