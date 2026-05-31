package com.xtc.dial.common.dataprovider;
import com.xtc.dial.common.RenderContext;
public class BatteryProvider {
    public BatteryProvider(RenderContext ctx) {}
    public int getLevel() { return 50; }
    public void listen() {}
    public void cancelListen() {}
    public void release() {}
}
