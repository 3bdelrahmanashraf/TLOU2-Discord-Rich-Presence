# Rebuilds the four 512x512 Discord assets from the source art.
#   pngs\Part_II_Ellie_infobox.png     -> assets\ellie.png
#   pngs\Abby_TLOU2_remaster.PNG.png   -> assets\abby.png
#   pngs\Part_II_Joel_infobox.png      -> assets\joel.png
#   assets\raw\tlou2.png (cover art)   -> assets\tlou2.png
# Run:  powershell -NoProfile -ExecutionPolicy Bypass -File make_assets.ps1
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class Art
{
    // Brightest content inside the top part of the frame = the subject.
    static Rectangle SubjectBox(Bitmap bmp, double topFraction)
    {
        int w = bmp.Width, h = bmp.Height;
        BitmapData data = bmp.LockBits(new Rectangle(0, 0, w, h),
                                       ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
        byte[] buf = new byte[data.Stride * h];
        Marshal.Copy(data.Scan0, buf, 0, buf.Length);
        bmp.UnlockBits(data);

        int limit = (int)(h * topFraction);
        int minX = w, maxX = -1, minY = h, maxY = -1;
        for (int y = 0; y < limit; y += 2)
        {
            int row = y * data.Stride;
            for (int x = 0; x < w; x += 2)
            {
                int i = row + x * 3;
                int lum = (buf[i + 2] * 30 + buf[i + 1] * 59 + buf[i] * 11) / 100;
                if (lum > 45)
                {
                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                }
            }
        }
        if (maxX < 0) return new Rectangle(0, 0, w, h);
        return Rectangle.FromLTRB(minX, minY, maxX + 1, maxY + 1);
    }

    public static void Crop(string src, string dst, int size)
    {
        using (var img = new Bitmap(src))
        {
            int side = Math.Min(img.Width, img.Height);
            Rectangle box = SubjectBox(img, 0.65);
            int left = (box.X + box.Width / 2) - side / 2;
            if (left < 0) left = 0;
            if (left + side > img.Width) left = img.Width - side;

            using (var outBmp = new Bitmap(size, size, PixelFormat.Format24bppRgb))
            using (var g = Graphics.FromImage(outBmp))
            {
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                g.DrawImage(img, new Rectangle(0, 0, size, size),
                            left, 0, side, side, GraphicsUnit.Pixel);
                outBmp.Save(dst, ImageFormat.Png);
            }
        }
    }
}
"@

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$assets = Join-Path $root "assets"
$pngs = Join-Path $root "pngs"
New-Item -ItemType Directory -Force -Path $assets | Out-Null

$jobs = @(
    @{ Src = Join-Path $assets "raw\tlou2.png";                Dst = "tlou2.png" },
    @{ Src = Join-Path $pngs "Part_II_Ellie_infobox.png";      Dst = "ellie.png" },
    @{ Src = Join-Path $pngs "Abby_TLOU2_remaster.PNG.png";    Dst = "abby.png"  },
    @{ Src = Join-Path $pngs "Part_II_Joel_infobox.png";       Dst = "joel.png"  }
)
foreach ($j in $jobs) {
    if (-not (Test-Path $j.Src)) { "missing source: $($j.Src)"; continue }
    $dst = Join-Path $assets $j.Dst
    [Art]::Crop($j.Src, $dst, 512)
    $img = [System.Drawing.Image]::FromFile($dst)
    "{0}: {1}x{2} {3:N0} bytes" -f $j.Dst, $img.Width, $img.Height, (Get-Item $dst).Length
    $img.Dispose()
}
