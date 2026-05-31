package com.xtc.dial.common;
import com.xtc.dial.iplugin.DialHostHolder;
public class DialHostHolderWrapper {
    private DialHostHolder mHostHolder;
    public DialHostHolderWrapper(DialHostHolder hostHolder) {
        this.mHostHolder = hostHolder;
    }
    public int callBackForIntWithDefault(int key, int defaultResultValue, Object... data) { return defaultResultValue; }
    public int callBackForInt(int key, Object... data) { return 0; }
    public String callBackForStringWithDefault(int key, String defaultResultValue, Object... data) { return defaultResultValue; }
    public String callBackForString(int key, Object... data) { return ""; }
    public double callBackForDoubleWithDefault(int key, double defaultResultValue, Object... data) { return defaultResultValue; }
    public double callBackForDouble(int key, Object... data) { return 0.0d; }
    public long callBackForLongWithDefault(int key, long defaultResultValue, Object... data) { return defaultResultValue; }
    public long callBackForLong(int key, Object... data) { return 0L; }
    public boolean callBackForBooleanWithDefault(int key, boolean defaultResultValue, Object... data) { return defaultResultValue; }
    public boolean callBackForBoolean(int key, Object... data) { return false; }
    public float callBackForFloatWithDefault(int key, float defaultResultValue, Object... data) { return defaultResultValue; }
    public float callBackForFloat(int key, Object... data) { return 0.0f; }
    public void callBack(int key, Object... data) {}
}
