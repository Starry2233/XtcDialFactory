package com.xtc.common;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.RelativeLayout;

/**
 * Stub for compilation only.
 * BaseDial extends RelativeLayout at runtime on device.
 */
public abstract class BaseDial extends RelativeLayout {
    public BaseDial(Context context) {
        this(context, null);
    }

    public BaseDial(Context context, AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public BaseDial(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
    }

    public void dealScreenOff() {}
    public void dealScreenOn() {}
    public void dealUpdateWeather(java.util.HashMap<Object, Object> map) {}

    public abstract String[] getMethodString();

    public int getWeatherAlarmType() { return 0; }

    public abstract void setShow(boolean show);

    public void startAnim() {}
    public void updateBattery(int level, int scale) {}
    public void updateLevel(int level) {}
    public void updateScore(int score) {}
    public void updateStep(int steps) {}

    public abstract void updateTime();
}
