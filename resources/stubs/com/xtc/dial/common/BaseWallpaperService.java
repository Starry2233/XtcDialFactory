package com.xtc.dial.common;

import android.content.Context;
import android.service.wallpaper.WallpaperService;
import android.util.Log;
import android.view.SurfaceHolder;
import com.xtc.dial.secure.DialRuntime;

public abstract class BaseWallpaperService extends WallpaperService {
    protected DialHostHolderWrapper hostHolder;
    protected Context mContext;

    protected abstract DialRuntime createDialRuntime();
    protected abstract WallpaperService.Engine createEngine();

    public BaseWallpaperService(DialHostHolderWrapper hostHolder, Context context) {
        this.hostHolder = hostHolder;
        this.mContext = context;
        attachBaseContext(context);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createDialRuntime().onWallpaperCreate();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
    }

    @Override
    public WallpaperService.Engine onCreateEngine() {
        return createEngine();
    }

    public abstract class BaseEngine extends WallpaperService.Engine {
        public String TAG;
        private long createTime;
        private boolean firstInvisible;
        private BaseRender mDialRender;

        protected abstract BaseRender getDialRender();

        public BaseEngine() {
            super();
            this.TAG = LogTag.getTag(BaseEngine.class.getSimpleName());
            this.firstInvisible = true;
            this.TAG = LogTag.getTag(getClass().getSimpleName());
        }

        @Override
        public void onCreate(SurfaceHolder surfaceHolder) {
            super.onCreate(surfaceHolder);
            Log.d(this.TAG, "onCreate");
            this.mDialRender = getDialRender();
        }

        @Override
        public void onSurfaceCreated(SurfaceHolder holder) {
            super.onSurfaceCreated(holder);
            Log.d(this.TAG, "onSurfaceCreated");
            if (this.mDialRender != null) {
                this.mDialRender.onSurfaceCreated(holder);
            }
            this.createTime = System.currentTimeMillis();
        }

        @Override
        public void onVisibilityChanged(boolean visible) {
            super.onVisibilityChanged(visible);
            Log.i(this.TAG, "onVisibilityChanged:" + visible);
            if (!visible && this.firstInvisible && System.currentTimeMillis() - this.createTime < 100) {
                Log.i(this.TAG, "firstInvisible");
                this.firstInvisible = false;
            } else if (this.mDialRender != null) {
                this.mDialRender.onVisibilityChanged(visible);
            }
        }

        @Override
        public void onSurfaceChanged(SurfaceHolder holder, int format, int width, int height) {
            super.onSurfaceChanged(holder, format, width, height);
            Log.i(this.TAG, "onSurfaceChanged");
        }

        @Override
        public void onSurfaceDestroyed(SurfaceHolder holder) {
            super.onSurfaceDestroyed(holder);
            Log.i(this.TAG, "onSurfaceDestroyed");
            if (this.mDialRender != null) {
                this.mDialRender.onDestroy();
            }
        }

        @Override
        public void onDestroy() {
            super.onDestroy();
            Log.i(this.TAG, "onDestroy");
        }
    }
}
