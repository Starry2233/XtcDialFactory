"""Generate dial framework stubs for javac compilation."""
import os

stubs_base = os.path.join(os.path.dirname(__file__), "..", "resources", "stubs")

stubs = {
    # com.xtc.dial.common
    "com/xtc/dial/common/BasePlugin.java": """\
package com.xtc.dial.common;
import android.service.wallpaper.WallpaperService;
public abstract class BasePlugin {
    public DialHostHolderWrapper mHostHolder;
    public android.content.Context context;
    public abstract WallpaperService i2GetWallpaperService();
}
""",
    "com/xtc/dial/common/BaseRender.java": """\
package com.xtc.dial.common;
import android.content.Context;
public abstract class BaseRender {
    protected Context mContext;
    protected android.content.res.Resources mResources;
    protected DialHostHolderWrapper hostHolder;
    protected RenderContext renderContext;
    public String TAG = "BaseRender";
    public long animInterval = 600000;
    public BaseRender(Context context, DialHostHolderWrapper hostHolder) {}
    protected void initMetricsFromConfig() {}
    protected void configInit() {}
    protected void addRenderModule(BaseModuleRender module) {}
    public void refreshFrame(long time) {}
    public boolean isAnimaRunning() { return false; }
    public void onTouchEvent(android.view.MotionEvent event) {}
}
""",
    "com/xtc/dial/common/BaseModuleRender.java": """\
package com.xtc.dial.common;
import android.content.Context;
import android.content.res.Resources;
public abstract class BaseModuleRender {
    protected Context mContext;
    protected Resources mResources;
    protected boolean isAnimaRunning = false;
    public BaseModuleRender(RenderContext renderContext) {
        this.mContext = renderContext != null ? renderContext.mContext : null;
        this.mResources = mContext != null ? mContext.getResources() : null;
    }
    public void drawFrame(CustomCanvas canvas, long time) {}
    public void onDestroy() {}
    public void whenVisible() {}
    public void whenInvisible() {}
    public boolean isAnimaRunning() { return this.isAnimaRunning; }
}
""",
    "com/xtc/dial/common/BaseWallpaperService.java": """\
package com.xtc.dial.common;
import android.content.Context;
import android.service.wallpaper.WallpaperService;
import android.view.MotionEvent;
public class BaseWallpaperService extends WallpaperService {
    public Context mContext;
    public DialHostHolderWrapper hostHolder;
    public BaseWallpaperService() {}
    public class BaseEngine extends WallpaperService.Engine {
        protected BaseRender getDialRender() { return null; }
        public void onTouchEvent(MotionEvent event) { super.onTouchEvent(event); }
    }
}
""",
    "com/xtc/dial/common/CustomCanvas.java": """\
package com.xtc.dial.common;
import android.graphics.*;
public class CustomCanvas {
    public void setDrawFilter(PaintFlagsDrawFilter filter) {}
    public void drawBitmap(Bitmap bitmap, float x, float y, Paint paint) {}
}
""",
    "com/xtc/dial/common/LogTag.java": """\
package com.xtc.dial.common;
public class LogTag {
    public static String getTag(String name) { return name; }
}
""",
    "com/xtc/dial/common/RenderContext.java": """\
package com.xtc.dial.common;
import android.content.Context;
public class RenderContext {
    public Context mContext;
    public RenderContext(Context context) { this.mContext = context; }
}
""",
    "com/xtc/dial/common/DialHostHolderWrapper.java": """\
package com.xtc.dial.common;
public class DialHostHolderWrapper {
    public int callBackForIntWithDefault(int type, int defaultVal, Object... args) { return defaultVal; }
}
""",
    # com.xtc.dial.common.util
    "com/xtc/dial/common/util/BitmapManager.java": """\
package com.xtc.dial.common.util;
import android.content.Context;
import android.graphics.Bitmap;
public class BitmapManager {
    public BitmapManager(Context context, String pkg) {}
    public Bitmap getBitmapByName(Context context, String name) { return null; }
    public Bitmap getBitmapCache(int id) { return null; }
    public Bitmap getTimeBitmap(int num) { return null; }
    public Bitmap getTimeSeparateBitmap() { return null; }
    public Bitmap getDateBitmap(int num) { return null; }
    public Bitmap getDateSeparateBitmap() { return null; }
    public Bitmap getWeekBitmap(int num) { return null; }
}
""",
    "com/xtc/dial/common/util/BehaviorAgent.java": """\
package com.xtc.dial.common.util;
import com.xtc.dial.common.DialHostHolderWrapper;
public class BehaviorAgent {
    public BehaviorAgent(DialHostHolderWrapper holder) {}
    public boolean recordBehavior(String function, String data) { return true; }
}
""",
    "com/xtc/dial/common/util/DialogAgent.java": """\
package com.xtc.dial.common.util;
import com.xtc.dial.common.DialHostHolderWrapper;
public class DialogAgent {
    public DialogAgent(DialHostHolderWrapper holder) {}
    public String buildInstallDialogJson(String pkg, String app, String func) { return "{}"; }
    public boolean showClickDialog(String json) { return true; }
}
""",
    "com/xtc/dial/common/util/SharedManager.java": """\
package com.xtc.dial.common.util;
import com.xtc.dial.common.DialHostHolderWrapper;
public class SharedManager {
    public SharedManager(DialHostHolderWrapper holder) {}
    public int getInt(String key, int def) { return def; }
    public void saveInt(String key, int value) {}
}
""",
    "com/xtc/dial/common/util/TypedValueCompat.java": """\
package com.xtc.dial.common.util;
import android.content.Context;
import android.util.DisplayMetrics;
public class TypedValueCompat {
    public static void initMetrics(Context context, DisplayMetrics dm, int imgSize, int planSize) {}
    public static float applyDimensionDip(float value) { return value; }
}
""",
    "com/xtc/dial/common/util/ComponentDrawer.java": """\
package com.xtc.dial.common.util;
import android.graphics.Paint;
import com.xtc.dial.common.CustomCanvas;
public class ComponentDrawer {
    public static void drawBattery(BitmapManager mgr, int level, CustomCanvas canvas, Paint paint, int x, int y, int[] params) {}
}
""",
    # com.xtc.dial.common.dataprovider
    "com/xtc/dial/common/dataprovider/TimeProvider.java": """\
package com.xtc.dial.common.dataprovider;
import com.xtc.dial.common.RenderContext;
public class TimeProvider {
    public TimeProvider(RenderContext ctx) {}
    public void refresh() {}
    public void listen() {}
    public void cancelListen() {}
    public void release() {}
    public int getNumHour1() { return 0; }
    public int getNumHour2() { return 0; }
    public int getMinute1() { return 0; }
    public int getMinute2() { return 0; }
    public int getMonth1()  { return 0; }
    public int getMonth2()  { return 0; }
    public int getDay1()    { return 0; }
    public int getDay2()    { return 0; }
    public int getWeek()    { return 0; }
}
""",
    "com/xtc/dial/common/dataprovider/BatteryProvider.java": """\
package com.xtc.dial.common.dataprovider;
import com.xtc.dial.common.RenderContext;
public class BatteryProvider {
    public BatteryProvider(RenderContext ctx) {}
    public int getLevel() { return 50; }
    public void listen() {}
    public void cancelListen() {}
    public void release() {}
}
""",
    # com.xtc.dial.secure
    "com/xtc/dial/secure/DialRuntime.java": """\
package com.xtc.dial.secure;
public class DialRuntime {}
""",
    "com/xtc/dial/secure/DialNormalRuntimeX.java": """\
package com.xtc.dial.secure;
public class DialNormalRuntimeX extends DialRuntime {}
""",
}

i = 0
for path, content in stubs.items():
    full_path = os.path.join(stubs_base, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    i += 1
    print(f"  [{i:2d}] {path}")

print(f"\nDone: {i} stubs created under {stubs_base}")
