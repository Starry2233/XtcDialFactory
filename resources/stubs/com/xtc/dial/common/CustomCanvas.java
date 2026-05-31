package com.xtc.dial.common;

import android.annotation.SuppressLint;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.DrawFilter;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.os.Build;
import com.xtc.dial.common.util.TypedValueCompat;

public class CustomCanvas {
    private Canvas mCanvas;
    private boolean valid = true;

    public void setCanvas(Canvas canvas) { this.mCanvas = canvas; }
    public void setValid(boolean valid) { this.valid = valid; }

    public void setDrawFilter(DrawFilter filter) {
        if (mCanvas != null && valid) mCanvas.setDrawFilter(filter);
    }

    public void drawBitmap(Bitmap bitmap, float left, float top, Paint paint) {
        if (mCanvas != null && valid)
            mCanvas.drawBitmap(bitmap, TypedValueCompat.applyDimensionDip(left), TypedValueCompat.applyDimensionDip(top), paint);
    }

    public void drawBitmap(Bitmap bitmap, Rect src, RectF dst, Paint paint) {
        if (mCanvas != null && valid) mCanvas.drawBitmap(bitmap, src, dst, paint);
    }

    public void drawBitmap(Bitmap bitmap, Rect src, Rect dst, Paint paint) {
        if (mCanvas != null && valid) mCanvas.drawBitmap(bitmap, src, dst, paint);
    }

    public void drawBitmap(Bitmap bitmap, Matrix matrix, Paint paint) {
        if (mCanvas != null && valid) mCanvas.drawBitmap(bitmap, matrix, paint);
    }

    public void drawText(String text, float x, float y, Paint paint) {
        if (mCanvas != null && valid)
            mCanvas.drawText(text, TypedValueCompat.applyDimensionDip(x), TypedValueCompat.applyDimensionDip(y), paint);
    }

    public void drawArc(RectF oval, float startAngle, float sweepAngle, boolean useCenter, Paint paint) {
        if (mCanvas != null && valid) mCanvas.drawArc(oval, startAngle, sweepAngle, useCenter, paint);
    }

    public void drawPath(Path path, Paint paint) {
        if (mCanvas != null && valid) mCanvas.drawPath(path, paint);
    }

    public void drawCircle(float cx, float cy, float radius, Paint paint) {
        if (mCanvas != null && valid)
            mCanvas.drawCircle(TypedValueCompat.applyDimensionDip(cx), TypedValueCompat.applyDimensionDip(cy), TypedValueCompat.applyDimensionDip(radius), paint);
    }

    public void drawColor(int color) {
        if (mCanvas != null && valid) mCanvas.drawColor(color);
    }

    public void restore() { if (mCanvas != null && valid) mCanvas.restore(); }
    public void save() { if (mCanvas != null && valid) mCanvas.save(); }

    @SuppressLint({"NewApi"})
    public void saveLayer(float left, float top, float right, float bottom, Paint paint) {
        if (mCanvas != null && valid) mCanvas.saveLayer(left, top, right, bottom, paint);
    }

    public Canvas getRealCanvas() { return mCanvas; }
}
