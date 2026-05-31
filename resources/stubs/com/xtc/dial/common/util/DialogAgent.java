package com.xtc.dial.common.util;
import com.xtc.dial.common.DialHostHolderWrapper;
public class DialogAgent {
    public DialogAgent(DialHostHolderWrapper holder) {}
    public String buildInstallDialogJson(String pkg, String app, String func) { return "{}"; }
    public boolean showClickDialog(String json) { return true; }
}
