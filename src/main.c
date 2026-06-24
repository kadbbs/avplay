#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/audio_fifo.h>
#include <libavutil/channel_layout.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
#include <libavutil/samplefmt.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>

typedef struct Options {
    const char *input;
    const char *output;
    const char *cover;
    const char *report;
    int width;
    int video_bitrate;
    int audio_bitrate;
    int audio_rate;
} Options;

typedef struct StreamCtx {
    int index;
    AVStream *stream;
    AVCodecContext *dec;
} StreamCtx;

typedef struct App {
    Options opt;
    AVFormatContext *ifmt;
    AVFormatContext *ofmt;
    StreamCtx vin;
    StreamCtx ain;
    AVStream *vout;
    AVStream *aout;
    AVCodecContext *venc;
    AVCodecContext *aenc;
    struct SwsContext *sws_yuv;
    struct SwsContext *sws_rgb;
    SwrContext *swr;
    AVAudioFifo *fifo;
    int have_video;
    int have_audio;
    int wrote_cover;
    int64_t packets;
    int64_t video_frames;
    int64_t audio_frames;
    int64_t video_pts;
    int64_t audio_pts;
} App;

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
            "  %s normalize <input> <output.mp4> [--width N] [--cover cover.ppm] [--report report.json]\n",
            argv0);
}

static int parse_options(int argc, char **argv, Options *opt)
{
    memset(opt, 0, sizeof(*opt));
    opt->width = 1280;
    opt->video_bitrate = 2500;
    opt->audio_bitrate = 128;
    opt->audio_rate = 48000;
    if (argc < 4 || strcmp(argv[1], "normalize") != 0) return AVERROR(EINVAL);
    opt->input = argv[2];
    opt->output = argv[3];
    for (int i = 4; i < argc; i++) {
        if (strcmp(argv[i], "--width") == 0 && i + 1 < argc) opt->width = atoi(argv[++i]);
        else if (strcmp(argv[i], "--cover") == 0 && i + 1 < argc) opt->cover = argv[++i];
        else if (strcmp(argv[i], "--report") == 0 && i + 1 < argc) opt->report = argv[++i];
        else return AVERROR(EINVAL);
    }
    return 0;
}

static void cleanup(App *app)
{
    if (app->ofmt && !(app->ofmt->oformat->flags & AVFMT_NOFILE)) avio_closep(&app->ofmt->pb);
    sws_freeContext(app->sws_yuv);
    sws_freeContext(app->sws_rgb);
    swr_free(&app->swr);
    av_audio_fifo_free(app->fifo);
    avcodec_free_context(&app->vin.dec);
    avcodec_free_context(&app->ain.dec);
    avcodec_free_context(&app->venc);
    avcodec_free_context(&app->aenc);
    avformat_close_input(&app->ifmt);
    avformat_free_context(app->ofmt);
}

static int open_decoder(AVFormatContext *fmt, enum AVMediaType type, StreamCtx *s)
{
    int ret;
    const AVCodec *codec = NULL;
    memset(s, 0, sizeof(*s));
    s->index = -1;
    ret = av_find_best_stream(fmt, type, -1, -1, &codec, 0);
    if (ret < 0) return ret;
    s->index = ret;
    s->stream = fmt->streams[s->index];
    s->dec = avcodec_alloc_context3(codec);
    if (!s->dec) return AVERROR(ENOMEM);
    ret = avcodec_parameters_to_context(s->dec, s->stream->codecpar);
    if (ret < 0) return ret;
    return avcodec_open2(s->dec, codec, NULL);
}

static int even(int value) { return value > 2 ? value & ~1 : 2; }

static AVRational video_time_base(StreamCtx *s)
{
    AVRational rate = s->stream->avg_frame_rate.num > 0 ? s->stream->avg_frame_rate : s->stream->r_frame_rate;
    if (rate.num <= 0 || rate.den <= 0) rate = (AVRational){25, 1};
    return av_inv_q(rate);
}

static int add_video(App *app)
{
    int ret;
    const AVCodec *codec = avcodec_find_encoder_by_name("libx264");
    int w = app->vin.dec->width;
    int h = app->vin.dec->height;
    if (!codec) codec = avcodec_find_encoder(AV_CODEC_ID_H264);
    if (!codec) return AVERROR_ENCODER_NOT_FOUND;
    if (w > app->opt.width) {
        h = (int)((int64_t)h * app->opt.width / w);
        w = app->opt.width;
    }
    w = even(w);
    h = even(h);
    app->venc = avcodec_alloc_context3(codec);
    if (!app->venc) return AVERROR(ENOMEM);
    app->venc->width = w;
    app->venc->height = h;
    app->venc->pix_fmt = AV_PIX_FMT_YUV420P;
    app->venc->time_base = video_time_base(&app->vin);
    app->venc->framerate = av_inv_q(app->venc->time_base);
    app->venc->bit_rate = (int64_t)app->opt.video_bitrate * 1000;
    app->venc->gop_size = 60;
    if (app->ofmt->oformat->flags & AVFMT_GLOBALHEADER) app->venc->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    av_opt_set(app->venc->priv_data, "preset", "veryfast", 0);
    ret = avcodec_open2(app->venc, codec, NULL);
    if (ret < 0) return ret;
    app->vout = avformat_new_stream(app->ofmt, NULL);
    if (!app->vout) return AVERROR(ENOMEM);
    app->vout->time_base = app->venc->time_base;
    ret = avcodec_parameters_from_context(app->vout->codecpar, app->venc);
    if (ret < 0) return ret;
    app->sws_yuv = sws_getContext(app->vin.dec->width, app->vin.dec->height, app->vin.dec->pix_fmt,
                                  w, h, app->venc->pix_fmt, SWS_BICUBIC, NULL, NULL, NULL);
    if (!app->sws_yuv) return AVERROR(EINVAL);
    if (app->opt.cover) {
        app->sws_rgb = sws_getContext(app->vin.dec->width, app->vin.dec->height, app->vin.dec->pix_fmt,
                                      w, h, AV_PIX_FMT_RGB24, SWS_BILINEAR, NULL, NULL, NULL);
        if (!app->sws_rgb) return AVERROR(EINVAL);
    }
    return 0;
}

static enum AVSampleFormat choose_sample_fmt(const AVCodec *codec)
{
    if (!codec->sample_fmts) return AV_SAMPLE_FMT_FLTP;
    for (const enum AVSampleFormat *p = codec->sample_fmts; *p != AV_SAMPLE_FMT_NONE; p++) {
        if (*p == AV_SAMPLE_FMT_FLTP) return *p;
    }
    return codec->sample_fmts[0];
}

static int add_audio(App *app)
{
    int ret;
    const AVCodec *codec = avcodec_find_encoder(AV_CODEC_ID_AAC);
    if (!codec) return AVERROR_ENCODER_NOT_FOUND;
    app->aenc = avcodec_alloc_context3(codec);
    if (!app->aenc) return AVERROR(ENOMEM);
    app->aenc->sample_rate = app->opt.audio_rate;
    app->aenc->sample_fmt = choose_sample_fmt(codec);
    app->aenc->bit_rate = (int64_t)app->opt.audio_bitrate * 1000;
    app->aenc->time_base = (AVRational){1, app->aenc->sample_rate};
    av_channel_layout_default(&app->aenc->ch_layout, 2);
    if (app->ofmt->oformat->flags & AVFMT_GLOBALHEADER) app->aenc->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    ret = avcodec_open2(app->aenc, codec, NULL);
    if (ret < 0) return ret;
    app->aout = avformat_new_stream(app->ofmt, NULL);
    if (!app->aout) return AVERROR(ENOMEM);
    app->aout->time_base = app->aenc->time_base;
    ret = avcodec_parameters_from_context(app->aout->codecpar, app->aenc);
    if (ret < 0) return ret;
    ret = swr_alloc_set_opts2(&app->swr, &app->aenc->ch_layout, app->aenc->sample_fmt, app->aenc->sample_rate,
                              &app->ain.dec->ch_layout, app->ain.dec->sample_fmt, app->ain.dec->sample_rate, 0, NULL);
    if (ret < 0) return ret;
    ret = swr_init(app->swr);
    if (ret < 0) return ret;
    app->fifo = av_audio_fifo_alloc(app->aenc->sample_fmt, app->aenc->ch_layout.nb_channels,
                                    app->aenc->frame_size > 0 ? app->aenc->frame_size : 1024);
    return app->fifo ? 0 : AVERROR(ENOMEM);
}

static int write_packet(App *app, AVCodecContext *enc, AVStream *stream, AVPacket *pkt)
{
    av_packet_rescale_ts(pkt, enc->time_base, stream->time_base);
    pkt->stream_index = stream->index;
    return av_interleaved_write_frame(app->ofmt, pkt);
}

static int encode(App *app, AVCodecContext *enc, AVStream *stream, AVFrame *frame)
{
    int ret = avcodec_send_frame(enc, frame);
    AVPacket *pkt = av_packet_alloc();
    if (ret < 0 || !pkt) return ret < 0 ? ret : AVERROR(ENOMEM);
    while ((ret = avcodec_receive_packet(enc, pkt)) >= 0) {
        ret = write_packet(app, enc, stream, pkt);
        av_packet_unref(pkt);
        if (ret < 0) break;
    }
    av_packet_free(&pkt);
    return ret == AVERROR(EAGAIN) || ret == AVERROR_EOF ? 0 : ret;
}

static AVFrame *video_frame(enum AVPixelFormat fmt, int w, int h)
{
    AVFrame *f = av_frame_alloc();
    if (!f) return NULL;
    f->format = fmt;
    f->width = w;
    f->height = h;
    if (av_frame_get_buffer(f, 32) < 0) av_frame_free(&f);
    return f;
}

static int write_cover(App *app, AVFrame *src)
{
    FILE *fp;
    uint8_t *rgb[4] = {0};
    int linesize[4] = {0};
    int ret;
    if (!app->opt.cover || app->wrote_cover) return 0;
    ret = av_image_alloc(rgb, linesize, app->venc->width, app->venc->height, AV_PIX_FMT_RGB24, 1);
    if (ret < 0) return ret;
    sws_scale(app->sws_rgb, (const uint8_t * const *)src->data, src->linesize, 0, src->height, rgb, linesize);
    fp = fopen(app->opt.cover, "wb");
    if (!fp) { av_freep(&rgb[0]); return AVERROR(errno); }
    fprintf(fp, "P6\n%d %d\n255\n", app->venc->width, app->venc->height);
    for (int y = 0; y < app->venc->height; y++) fwrite(rgb[0] + y * linesize[0], 1, (size_t)app->venc->width * 3, fp);
    fclose(fp);
    av_freep(&rgb[0]);
    app->wrote_cover = 1;
    return 0;
}

static int process_video(App *app, AVFrame *decoded)
{
    int ret;
    AVFrame *out = video_frame(app->venc->pix_fmt, app->venc->width, app->venc->height);
    if (!out) return AVERROR(ENOMEM);
    ret = write_cover(app, decoded);
    if (ret < 0) { av_frame_free(&out); return ret; }
    sws_scale(app->sws_yuv, (const uint8_t * const *)decoded->data, decoded->linesize,
              0, decoded->height, out->data, out->linesize);
    out->pts = app->video_pts++;
    app->video_frames++;
    ret = encode(app, app->venc, app->vout, out);
    av_frame_free(&out);
    return ret;
}

static AVFrame *audio_frame(AVCodecContext *enc, int samples)
{
    AVFrame *f = av_frame_alloc();
    if (!f) return NULL;
    f->format = enc->sample_fmt;
    f->sample_rate = enc->sample_rate;
    f->nb_samples = samples;
    if (av_channel_layout_copy(&f->ch_layout, &enc->ch_layout) < 0 || av_frame_get_buffer(f, 0) < 0) av_frame_free(&f);
    return f;
}

static int encode_fifo(App *app, int flush)
{
    int ret = 0;
    int frame_size = app->aenc->frame_size > 0 ? app->aenc->frame_size : 1024;
    while (av_audio_fifo_size(app->fifo) >= frame_size || (flush && av_audio_fifo_size(app->fifo) > 0)) {
        int samples = av_audio_fifo_size(app->fifo);
        AVFrame *frame;
        if (!flush || samples > frame_size) samples = frame_size;
        frame = audio_frame(app->aenc, samples);
        if (!frame) return AVERROR(ENOMEM);
        ret = av_audio_fifo_read(app->fifo, (void **)frame->data, samples);
        if (ret < 0) { av_frame_free(&frame); return ret; }
        frame->pts = app->audio_pts;
        app->audio_pts += frame->nb_samples;
        app->audio_frames++;
        ret = encode(app, app->aenc, app->aout, frame);
        av_frame_free(&frame);
        if (ret < 0) return ret;
    }
    return 0;
}

static int process_audio(App *app, AVFrame *decoded)
{
    int ret, linesize = 0;
    uint8_t **converted = NULL;
    int samples = (int)av_rescale_rnd(swr_get_delay(app->swr, decoded->sample_rate) + decoded->nb_samples,
                                      app->aenc->sample_rate, decoded->sample_rate, AV_ROUND_UP);
    ret = av_samples_alloc_array_and_samples(&converted, &linesize, app->aenc->ch_layout.nb_channels,
                                             samples, app->aenc->sample_fmt, 0);
    if (ret < 0) return ret;
    ret = swr_convert(app->swr, converted, samples, (const uint8_t **)decoded->extended_data, decoded->nb_samples);
    if (ret > 0) {
        int grow = av_audio_fifo_realloc(app->fifo, av_audio_fifo_size(app->fifo) + ret);
        if (grow < 0) {
            ret = grow;
            goto done;
        }
        av_audio_fifo_write(app->fifo, (void **)converted, ret);
        ret = encode_fifo(app, 0);
    }
done:
    av_freep(&converted[0]);
    av_freep(&converted);
    return ret < 0 ? ret : 0;
}

static int decode_packet(App *app, StreamCtx *s, AVPacket *pkt)
{
    int ret = avcodec_send_packet(s->dec, pkt);
    AVFrame *frame = av_frame_alloc();
    if (ret < 0 || !frame) return ret < 0 ? ret : AVERROR(ENOMEM);
    while ((ret = avcodec_receive_frame(s->dec, frame)) >= 0) {
        ret = s->dec->codec_type == AVMEDIA_TYPE_VIDEO ? process_video(app, frame) : process_audio(app, frame);
        av_frame_unref(frame);
        if (ret < 0) break;
    }
    av_frame_free(&frame);
    return ret == AVERROR(EAGAIN) || ret == AVERROR_EOF ? 0 : ret;
}

static int write_report(App *app)
{
    FILE *fp;
    if (!app->opt.report) return 0;
    fp = fopen(app->opt.report, "w");
    if (!fp) return AVERROR(errno);
    fprintf(fp,
            "{\n"
            "  \"input\": \"%s\",\n"
            "  \"output\": \"%s\",\n"
            "  \"packets_read\": %" PRId64 ",\n"
            "  \"video_frames\": %" PRId64 ",\n"
            "  \"audio_frames\": %" PRId64 ",\n"
            "  \"width\": %d,\n"
            "  \"height\": %d,\n"
            "  \"audio_rate\": %d\n"
            "}\n",
            app->opt.input, app->opt.output, app->packets, app->video_frames, app->audio_frames,
            app->have_video ? app->venc->width : 0, app->have_video ? app->venc->height : 0,
            app->have_audio ? app->aenc->sample_rate : 0);
    fclose(fp);
    return 0;
}

static int normalize(App *app)
{
    int ret;
    AVPacket *pkt;
    ret = avformat_open_input(&app->ifmt, app->opt.input, NULL, NULL);
    if (ret < 0) return fail("Could not open input", ret);
    ret = avformat_find_stream_info(app->ifmt, NULL);
    if (ret < 0) return fail("Could not read input info", ret);
    ret = avformat_alloc_output_context2(&app->ofmt, NULL, "mp4", app->opt.output);
    if (ret < 0) return fail("Could not create output", ret);
    if (open_decoder(app->ifmt, AVMEDIA_TYPE_VIDEO, &app->vin) >= 0) {
        app->have_video = 1;
        if ((ret = add_video(app)) < 0) return fail("Could not add video output", ret);
    }
    if (open_decoder(app->ifmt, AVMEDIA_TYPE_AUDIO, &app->ain) >= 0) {
        app->have_audio = 1;
        if ((ret = add_audio(app)) < 0) return fail("Could not add audio output", ret);
    }
    if (!app->have_video && !app->have_audio) return fail("No audio/video stream", AVERROR_STREAM_NOT_FOUND);
    if (!(app->ofmt->oformat->flags & AVFMT_NOFILE)) {
        ret = avio_open(&app->ofmt->pb, app->opt.output, AVIO_FLAG_WRITE);
        if (ret < 0) return fail("Could not open output file", ret);
    }
    ret = avformat_write_header(app->ofmt, NULL);
    if (ret < 0) return fail("Could not write header", ret);
    pkt = av_packet_alloc();
    if (!pkt) return AVERROR(ENOMEM);
    while ((ret = av_read_frame(app->ifmt, pkt)) >= 0) {
        app->packets++;
        if (app->have_video && pkt->stream_index == app->vin.index) ret = decode_packet(app, &app->vin, pkt);
        else if (app->have_audio && pkt->stream_index == app->ain.index) ret = decode_packet(app, &app->ain, pkt);
        else ret = 0;
        av_packet_unref(pkt);
        if (ret < 0) break;
    }
    av_packet_free(&pkt);
    if (app->have_video) {
        decode_packet(app, &app->vin, NULL);
        encode(app, app->venc, app->vout, NULL);
    }
    if (app->have_audio) {
        decode_packet(app, &app->ain, NULL);
        encode_fifo(app, 1);
        encode(app, app->aenc, app->aout, NULL);
    }
    ret = av_write_trailer(app->ofmt);
    if (ret < 0) return fail("Could not write trailer", ret);
    ret = write_report(app);
    if (ret < 0) return fail("Could not write report", ret);
    printf("Normalized: %s -> %s\n", app->opt.input, app->opt.output);
    return 0;
}

int main(int argc, char **argv)
{
    App app;
    int ret;
    memset(&app, 0, sizeof(app));
    ret = parse_options(argc, argv, &app.opt);
    if (ret < 0) { usage(argv[0]); return 1; }
    ret = normalize(&app);
    cleanup(&app);
    return ret < 0 ? 1 : 0;
}
