package com.xtc.dial.common.util;
import com.xtc.dial.common.DialHostHolderWrapper;
public class SharedManager {
    public SharedManager(DialHostHolderWrapper holder) {}
    public int getInt(String key, int def) { return def; }
    public void saveInt(String key, int value) {}
}
