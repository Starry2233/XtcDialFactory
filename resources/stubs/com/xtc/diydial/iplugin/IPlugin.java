package com.xtc.diydial.iplugin;

import android.content.Context;
import android.view.View;
import java.lang.reflect.InvocationTargetException;

/**
 * Stub matching the device's IPlugin interface.
 * Loaded by the launcher's ComposePluginLoader via DexClassLoader.
 */
public interface IPlugin {
    String getSourceName();

    /**
     * @param extra JSON string from element config, e.g. "{\"previewStyle\":5,\"runMode\":2}"
     */
    View getView(String extra);

    /**
     * @param context Application context
     * @param apkPath Path to the .pl APK file on device
     */
    void initPlugin(Context context, String apkPath) throws IllegalAccessException, NoSuchMethodException, InstantiationException, InvocationTargetException;

    void registerCallback(IMessageCallback callback);

    Object sendMessage(int action, Object data);

    void sendMessage(int action, Object data, IMessageCallback callback);
}
