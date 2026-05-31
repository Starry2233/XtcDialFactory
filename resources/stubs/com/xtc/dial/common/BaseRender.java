package com.xtc.dial.common;

import android.content.Context;
import android.graphics.Canvas;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Message;
import android.util.Log;
import android.view.SurfaceHolder;
import com.xtc.dial.common.util.TypedValueCompat;

import java.util.ArrayList;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

public abstract class BaseRender implements Handler.Callback, AnimalTrigger.ShowListener {
    private static final int MESSAGE_DRAW = 1001;
    private static final int MESSAGE_SHOW_ANIMATION = 1000;
    protected static String TAG = LogTag.getTag(BaseRender.class.getSimpleName());
    private AnimalTrigger animalTrigger;
    private long currentTime;
    protected Handler handler;
    private SurfaceHolder holder;
    protected DialHostHolderWrapper hostHolder;
    private boolean isAnimaRunning;
    private long lastScreenOnPlayAnimTime;
    private long lastUnlockPlayAnimTime;
    protected Context mContext;
    private CustomCanvas mCustomCanvas;
    private List<BaseModuleRender> mModuleRenders;
    protected RenderContext renderContext;
    private boolean visible;
    protected int timeRefreshInterval = 60000;
    protected int animInterval = 600000;
    protected int screenOnAnimInterval = 600000;
    protected boolean supportScreenOnAnim = false;
    protected boolean isSensorFlash = true;

    protected abstract void configInit();

    public BaseRender(Context context, DialHostHolderWrapper hostHolder) {
        TAG = LogTag.getTag(getClass().getSimpleName());
        this.mContext = context;
        this.hostHolder = hostHolder;
        initMetricsFromConfig();
        HandlerThread renderThread = new HandlerThread(TAG);
        renderThread.start();
        this.handler = new Handler(renderThread.getLooper(), this);
        HandlerThread dataThread = new HandlerThread("dial_dataThread");
        dataThread.start();
        Handler dataHandler = new Handler(dataThread.getLooper());
        this.renderContext = new RenderContext(dataHandler, context, hostHolder);
        this.mCustomCanvas = new CustomCanvas();
        this.mModuleRenders = new ArrayList<BaseModuleRender>();
        configInit();
    }

    protected void initMetricsFromConfig() {
        try {
            Context ctx = this.mContext;
            TypedValueCompat.initMetrics(ctx, ctx.getResources().getDisplayMetrics(),
                    ctx.getResources().getInteger(ctx.getResources().getIdentifier("image_size_416_468", "integer", ctx.getPackageName())),
                    ctx.getResources().getInteger(ctx.getResources().getIdentifier("design_plan_size_160", "integer", ctx.getPackageName())));
        } catch (Exception e) {
            Log.w(TAG, "initMetricsFromConfig: " + e.getMessage());
        }
    }

    protected void updateRefreshStrategy() {}

    protected void addRenderModule(BaseModuleRender baseModuleRender) {
        this.mModuleRenders.add(baseModuleRender);
    }

    protected int getAnimInterval() { return this.animInterval; }
    protected int getAnimationDrawInterval() { return 25; }
    protected int getScreenOnAnimInterval() { return this.screenOnAnimInterval; }
    protected boolean isSupportScreenOnAnim() { return this.supportScreenOnAnim; }

    protected boolean checkAnimation(int status) {
        if (1 == status) {
            int unlockAnimInterval = getAnimInterval();
            Log.d(TAG, "unlockAnimInterval = " + unlockAnimInterval);
            if (Math.abs(System.currentTimeMillis() - this.lastUnlockPlayAnimTime) < unlockAnimInterval) {
                Log.i(TAG, "上次解锁播放到这次间隔还没超过" + unlockAnimInterval);
                return false;
            }
            this.lastUnlockPlayAnimTime = System.currentTimeMillis();
            return true;
        }
        if (2 == status) {
            int screenOnAnimInterval = getScreenOnAnimInterval();
            if (Math.abs(System.currentTimeMillis() - this.lastScreenOnPlayAnimTime) < screenOnAnimInterval) {
                Log.i(TAG, "上次锁屏亮屏播放到这次间隔还没超过" + screenOnAnimInterval);
                return false;
            }
            this.lastScreenOnPlayAnimTime = System.currentTimeMillis();
            return true;
        }
        if (4 != status) return true;
        int unlockAnimInterval2 = getAnimInterval();
        if (Math.abs(System.currentTimeMillis() - this.lastUnlockPlayAnimTime) < unlockAnimInterval2) {
            Log.i(TAG, "上次解锁播放到这次间隔还没超过" + unlockAnimInterval2);
            return false;
        }
        this.lastUnlockPlayAnimTime = System.currentTimeMillis();
        return true;
    }

    public void showAnimation(int status) {
        if (this.isAnimaRunning) {
            Log.i(TAG, "show 正在播放动画不进入");
            return;
        }
        if (checkAnimation(status) && this.holder != null) {
            Log.i(TAG, "show 展示动画");
            this.currentTime = 0L;
            removeDrawMessage();
            Message message = Message.obtain();
            message.what = 1000;
            message.arg1 = status;
            this.handler.sendMessage(message);
        }
    }

    public void onSurfaceCreated(SurfaceHolder holder) {
        this.holder = holder;
        AnimalTrigger animalTrigger = new AnimalTrigger(this.mContext);
        this.animalTrigger = animalTrigger;
        animalTrigger.setShowListener(this);
        this.handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                BaseRender.this.showAnimation(1);
            }
        }, 900L);
    }

    public void onVisibilityChanged(boolean visible) {
        this.visible = visible;
        if (visible) {
            whenVisible();
        } else {
            whenInvisible();
        }
    }

    private void whenInvisible() {
        for (BaseModuleRender moduleRender : this.mModuleRenders) {
            moduleRender.whenInvisible();
        }
        removeDrawMessage();
        this.isAnimaRunning = false;
    }

    private void whenVisible() {
        for (BaseModuleRender moduleRender : this.mModuleRenders) {
            moduleRender.whenVisible();
        }
        refreshFrame(0L);
    }

    protected void refreshFrame(long delay) {
        if (this.isAnimaRunning) {
            Log.i(TAG, "动画正在进行");
            return;
        }
        this.handler.removeMessages(1001);
        this.handler.sendEmptyMessageDelayed(1001, delay);
    }

    public void onDestroy() {
        synchronized (this) {
            this.holder = null;
            this.mCustomCanvas.setValid(false);
            com.xtc.dial.common.util.BitmapCache.clear();
            if (this.animalTrigger != null) this.animalTrigger.release();
            for (BaseModuleRender moduleRender : this.mModuleRenders) {
                moduleRender.onDestroy();
            }
            this.handler.getLooper().quit();
            this.handler.removeCallbacksAndMessages(null);
        }
    }

    @Override
    public boolean handleMessage(Message msg) {
        int what = msg.what;
        if (what == 1000) {
            if (4 == msg.arg1 && (this.currentTime == 0 || isAnimaRunning())) {
                doDrawFrame(msg.arg1);
            } else {
                boolean z = this.visible;
                if (!z) {
                    this.isAnimaRunning = false;
                    Log.i(TAG, "不可见状态");
                } else if (z && (this.currentTime == 0 || isAnimaRunning())) {
                    doDrawFrame(msg.arg1);
                } else {
                    this.isAnimaRunning = false;
                    dealSensorDialAnimationEnd();
                    refreshFrame(0L);
                }
            }
        } else if (what == 1001) {
            for (BaseModuleRender mModuleRender : this.mModuleRenders) {
                mModuleRender.setStatus(msg.arg1);
            }
            drawFrame(100000L);
            if (this.visible) {
                refreshFrame(this.timeRefreshInterval);
            }
        }
        return false;
    }

    private void doDrawFrame(int state) {
        for (BaseModuleRender mModuleRender : this.mModuleRenders) {
            mModuleRender.setStatus(state);
        }
        this.isAnimaRunning = true;
        drawFrame(this.currentTime);
        this.currentTime += (long) getAnimationDrawInterval();
        this.handler.removeMessages(1000);
        Message message = Message.obtain();
        message.what = 1000;
        message.arg1 = state;
        this.handler.sendMessageDelayed(message, getAnimationDrawInterval());
    }

    private void dealSensorDialAnimationEnd() {
        updateRefreshStrategy();
        for (BaseModuleRender mModuleRender : this.mModuleRenders) {
            mModuleRender.setSensorFlash(this.isSensorFlash);
        }
        new Timer().schedule(new TimerTask() {
            @Override
            public void run() {
                for (BaseModuleRender mModuleRender2 : BaseRender.this.mModuleRenders) {
                    mModuleRender2.setSensorFlash(false);
                }
            }
        }, 1000L);
    }

    private void drawFrame(long time) {
        if (this.holder == null) {
            Log.i(TAG, "SurfaceHolder 未初始化");
            return;
        }
        synchronized (this) {
            try {
                if (!this.holder.getSurface().isValid()) {
                    Log.i(TAG, "surface is inValid");
                    return;
                }
                Canvas canvas = Build.VERSION.SDK_INT >= 26 ? this.holder.lockHardwareCanvas() : this.holder.lockCanvas();
                if (canvas == null) {
                    Log.i(TAG, "canvas is null");
                    return;
                }
                this.mCustomCanvas.setCanvas(canvas);
                realDrawFrame(this.mCustomCanvas, time);
                if (canvas != null) {
                    try {
                        if (this.holder.getSurface().isValid()) {
                            this.holder.unlockCanvasAndPost(canvas);
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "解锁画布异常", e);
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "绘制异常", e);
            }
        }
    }

    @Override
    public void slideUnlockShow() { showAnimation(1); }
    @Override
    public void pwdOrFaceUnLockShow() { showAnimation(4); }
    @Override
    public void screenOnShow() {
        if (!isSupportScreenOnAnim()) {
            Log.d(TAG, "当前表盘不支持锁屏亮屏播放动画...");
        } else {
            showAnimation(2);
        }
    }
    @Override
    public void onStateChange(int state) {}

    protected void realDrawFrame(CustomCanvas canvas, long time) {
        for (BaseModuleRender moduleRender : this.mModuleRenders) {
            if (moduleRender.isShow()) {
                moduleRender.drawFrame(canvas, time);
            }
        }
    }

    protected boolean isAnimaRunning() {
        for (BaseModuleRender moduleRender : this.mModuleRenders) {
            if (moduleRender.isShow() && moduleRender.isAnimaRunning()) return true;
        }
        return false;
    }

    private void removeDrawMessage() {
        this.handler.removeMessages(1001);
        this.handler.removeMessages(1000);
    }
}
