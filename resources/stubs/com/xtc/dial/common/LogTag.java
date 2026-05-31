package com.xtc.dial.common;

public class LogTag {
    public static String sourceName = "";

    public static void setSourceName(String sourceName2) { sourceName = sourceName2; }
    public static String getTag(String originTag) { return sourceName + "_" + originTag; }
}
