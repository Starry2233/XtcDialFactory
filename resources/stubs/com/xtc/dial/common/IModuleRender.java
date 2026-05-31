package com.xtc.dial.common;

interface IModuleRender {
    void drawFrame(CustomCanvas customCanvas, long j);
    void onDestroy();
    void whenInvisible();
    void whenVisible();
}
