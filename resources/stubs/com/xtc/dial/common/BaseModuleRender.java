package com.xtc.dial.common;

import android.content.Context;
import android.content.res.Resources;

public abstract class BaseModuleRender implements IModuleRender {
    private String TAG;
    protected boolean isAnimaRunning;
    protected boolean isDialAnimaRunning;
    protected boolean isSensorFlash;
    protected Context mContext;
    protected int mHeight;
    protected RenderContext mRenderContext;
    protected Resources mResources;
    protected int mWidth;
    protected int lastStatus = 2;
    protected int status = 1;
    private boolean isShow = true;

    public BaseModuleRender(RenderContext renderContext) {
        this.TAG = LogTag.getTag(BaseModuleRender.class.getSimpleName());
        this.TAG = LogTag.getTag(getClass().getSimpleName());
        this.mRenderContext = renderContext;
        Context context = renderContext.getContext();
        this.mContext = context;
        Resources resources = context.getResources();
        this.mResources = resources;
        this.mWidth = resources.getDisplayMetrics().widthPixels;
        this.mHeight = this.mResources.getDisplayMetrics().heightPixels;
    }

    public boolean isAnimaRunning() { return this.isAnimaRunning; }
    public void setStatus(int status) { this.status = status; }
    public boolean isSensorFlash() { return this.isSensorFlash; }
    public void setSensorFlash(boolean isSensorFlash) { this.isSensorFlash = isSensorFlash; }
    public int getStatus() { return this.status; }
    public void setShow(boolean show) { this.isShow = show; }
    public boolean isShow() { return this.isShow; }
}
