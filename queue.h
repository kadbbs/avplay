//
// Created by bbs on 24-4-14.
//

#ifndef PLAYER_QUEUE_H
#define PLAYER_QUEUE_H
#include <queue>
#include <condition_variable>

template <typename T>
class queue {
public:
    queue(){};
    ~queue(){};
    void Abort(){
        abort_=1;
        cond_.notify_all();
    }

    int Push(T val){
        std::lock_guard<std::mutex> lock(mutex_);
        if(1==abort_){
            return -1;
        }
        queue_.push(val);
        cond_.notify_one();
        return 0;
    }

    int Pop(T &val,const int timeout =0){
        std::unique_lock<std::mutex> lock(mutex_);
        cond_.wait_for(lock,std::chrono::microseconds(timeout),[this]{
            return !queue_.empty() |abort_;
        });
        if(1==abort_){
            return -1;

        }
        if(queue_.empty()){
            return -2;
        }

        val=queue_.front();
        queue_.pop();
        return 0;
    }

    int Front(T &val){
        std::lock_guard<std::mutex> lock(mutex_);
        if(1==abort_){
            return -1;
        }
        if(1==abort_){
            return -1;

        }
        if(queue_.empty()){
            return -2;
        }

        val=queue_.front();
        return 0;

    }
    int Size(){
        std::lock_guard<std::mutex> lock(mutex_);
        if(1==abort_){
            return -1;
        }
        return queue_.size();
    }

private:
    int abort_=0;
    std::mutex mutex_;
    std::condition_variable cond_;
    std::queue<T> queue_;
};


#endif //PLAYER_QUEUE_H
