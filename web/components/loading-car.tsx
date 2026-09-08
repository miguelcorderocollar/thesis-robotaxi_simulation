"use client";
import { useEffect, useRef } from "react";

export function LoadingCar({ paused }: { paused: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const node = canvas.current;
    if (!node) return;
    const context = node.getContext("2d");
    if (!context) return;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const image = new Image();
    let frame = 0,
      last = 0,
      visible = true,
      disposed = false;
    const points: [number, number][] = [];
    const draw = (time: number) => {
      if (disposed) return;
      context.clearRect(0, 0, 720, 240);
      const pulse = (time / 6500) % 1;
      for (const [x, y] of points) {
        const intensity =
          paused || reduced.matches
            ? 0
            : Math.max(0, 1 - Math.abs(x / 720 - pulse) / 0.12);
        context.fillStyle =
          intensity > 0.1
            ? `rgb(${150 + intensity * 105}, ${90 * (1 - intensity)}, ${90 * (1 - intensity)})`
            : "#777777";
        context.beginPath();
        context.arc(x, y, 1.2 + intensity, 0, Math.PI * 2);
        context.fill();
      }
    };
    const tick = (time: number) => {
      if (time - last > 1000 / 24) {
        draw(time);
        last = time;
      }
      frame = requestAnimationFrame(tick);
    };
    const sync = () => {
      cancelAnimationFrame(frame);
      draw(performance.now());
      if (
        !paused &&
        !reduced.matches &&
        visible &&
        !document.hidden &&
        points.length
      )
        frame = requestAnimationFrame(tick);
    };
    image.onload = () => {
      if (disposed) return;
      const mask = document.createElement("canvas");
      mask.width = 720;
      mask.height = 240;
      const ctx = mask.getContext("2d");
      if (!ctx) return;
      const scale = Math.min(680 / image.width, 200 / image.height);
      const w = image.width * scale,
        h = image.height * scale;
      ctx.drawImage(image, (720 - w) / 2, (240 - h) / 2, w, h);
      const data = ctx.getImageData(0, 0, 720, 240).data;
      for (let y = 0; y < 240; y += 3)
        for (let x = 0; x < 720; x += 3)
          if (data[(y * 720 + x) * 4 + 3] > 25) points.push([x, y]);
      node.style.opacity = "1";
      sync();
    };
    image.src = "/robotaxi-outline.svg";
    const observer = new IntersectionObserver((entries) => {
      visible = entries[0].isIntersecting;
      sync();
    });
    observer.observe(node);
    document.addEventListener("visibilitychange", sync);
    reduced.addEventListener("change", sync);
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener("visibilitychange", sync);
      reduced.removeEventListener("change", sync);
    };
  }, [paused]);
  return (
    <div className="halftone-car">
      <img src="/robotaxi-outline.svg" alt="" />
      <canvas ref={canvas} width={720} height={240} aria-hidden="true" />
    </div>
  );
}
