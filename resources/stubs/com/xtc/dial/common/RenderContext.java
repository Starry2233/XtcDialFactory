package com.xtc.dial.common;

import android.content.Context;
import android.os.Handler;

public class RenderContext {
    private Context mContext;
    private Handler mHandler;
    private DialHostHolderWrapper mHostHolder;

    public RenderContext(Handler handler, Context context, DialHostHolderWrapper hostHolder) {
        this.mHandler = handler;
        this.mContext = context;
        this.mHostHolder = hostHolder;
    }

    public Handler getHandler() { return mHandler; }
    public Context getContext() { return mContext; }
    public DialHostHolderWrapper getHostHolder() { return mHostHolder; }
}
