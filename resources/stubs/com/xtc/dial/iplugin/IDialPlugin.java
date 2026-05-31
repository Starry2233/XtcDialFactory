package com.xtc.dial.iplugin;
import android.content.Context;
import android.service.wallpaper.WallpaperService;
public interface IDialPlugin {
    void i1ContextInit(Context context);
    WallpaperService i2GetWallpaperService();
    void i3RegisterCallback(DialHostHolder dialHostHolder);
    Object i4SendMessage(int key, Object... message);
}
