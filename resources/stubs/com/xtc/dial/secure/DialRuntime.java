package com.xtc.dial.secure;
public abstract class DialRuntime {
    protected abstract void onCreate();
    public void onWallpaperCreate() {
        onCreate();
    }
}
