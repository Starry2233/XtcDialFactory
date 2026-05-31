package com.xtc.dial.common;

import android.content.Context;

public class AnimalTrigger {
    private ShowListener mShowListener;

    public interface ShowListener {
        void onStateChange(int state);
        void pwdOrFaceUnLockShow();
        void screenOnShow();
        void slideUnlockShow();
    }

    public AnimalTrigger(Context context) {
    }

    public void setShowListener(ShowListener listener) {
        this.mShowListener = listener;
    }

    public void release() {
        this.mShowListener = null;
    }
}
