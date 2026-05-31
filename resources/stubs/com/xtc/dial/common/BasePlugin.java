package com.xtc.dial.common;
import android.content.Context;
import android.service.wallpaper.WallpaperService;
import com.xtc.dial.iplugin.DialHostHolder;
import com.xtc.dial.iplugin.IDialPlugin;
public abstract class BasePlugin implements IDialPlugin {
    public static final String PREFIX = "com.xtc.dial.";
    public static final String SUFFIX = ".DialPlugin";
    protected Context context;
    protected DialHostHolder mHostCallback;
    public DialHostHolderWrapper mHostHolder;
    public BasePlugin() {
    }
    @Override
    public abstract WallpaperService i2GetWallpaperService();
    @Override
    public void i1ContextInit(Context context) {
        this.context = context;
    }
    @Override
    public void i3RegisterCallback(DialHostHolder callback) {
        this.mHostCallback = callback;
        this.mHostHolder = new DialHostHolderWrapper(this.mHostCallback);
    }
    @Override
    public Object i4SendMessage(int key, Object... message) {
        return null;
    }
}
