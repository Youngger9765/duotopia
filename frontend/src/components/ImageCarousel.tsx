import React, { useState, useRef, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";

interface ImageCarouselProps {
  images: { src: string; caption?: string }[];
}

export const ImageCarousel: React.FC<ImageCarouselProps> = ({ images }) => {
  const { t } = useTranslation();
  const [current, setCurrent] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  const goTo = useCallback(
    (idx: number) => {
      if (isTransitioning || idx === current) return;
      setIsTransitioning(true);
      setCurrent(idx);
      setTimeout(() => setIsTransitioning(false), 300);
    },
    [current, isTransitioning],
  );

  const prev = useCallback(
    () => goTo(current === 0 ? images.length - 1 : current - 1),
    [current, images.length, goTo],
  );

  const next = useCallback(
    () => goTo(current === images.length - 1 ? 0 : current + 1),
    [current, images.length, goTo],
  );

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current;
    if (Math.abs(diff) > 50) {
      if (diff > 0) next();
      else prev();
    }
  };

  return (
    <div className="w-full flex flex-col items-center">
      {/* Dot indicators */}
      <div className="flex gap-2.5 mb-3">
        {images.map((_, idx) => (
          <button
            key={idx}
            className={`w-3 h-3 rounded-full transition-all duration-300 ${
              current === idx
                ? "bg-blue-600 scale-125"
                : "bg-gray-300 hover:bg-gray-400"
            }`}
            onClick={() => goTo(idx)}
            aria-label={t("home.features.carousel.goToSlide", { number: idx + 1 })}
          />
        ))}
      </div>

      <div
        className="relative w-full flex items-center justify-center select-none"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Left arrow */}
        <button
          className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-transparent hover:bg-white/80 rounded-full p-2 hover:shadow-md transition-all"
          onClick={prev}
          aria-label={t("home.features.carousel.prev")}
        >
          <ChevronLeft className="h-6 w-6 text-gray-700" />
        </button>

        {/* Image */}
        <img
          src={images[current].src}
          alt={images[current].caption || `slide ${current + 1}`}
          className="w-full rounded-2xl transition-opacity duration-300"
          style={{ opacity: isTransitioning ? 0.6 : 1 }}
          draggable={false}
        />

        {/* Right arrow */}
        <button
          className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-transparent hover:bg-white/80 rounded-full p-2 hover:shadow-md transition-all"
          onClick={next}
          aria-label={t("home.features.carousel.next")}
        >
          <ChevronRight className="h-6 w-6 text-gray-700" />
        </button>
      </div>

      {/* Caption area */}
      <div className="mt-2 min-h-[2.5rem] text-center text-lg text-gray-700 whitespace-pre-line">
        {images[current].caption || (
          <span className="text-gray-400">&nbsp;</span>
        )}
      </div>
    </div>
  );
};
