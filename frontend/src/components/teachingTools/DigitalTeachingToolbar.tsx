import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Timer,
  Dice5,
  Play,
  Square,
  X,
  GripHorizontal,
  Triangle,
  Pencil,
  Eraser,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import './styles/toolbar.css';

// Timer Component
const TimerTool: React.FC<{
  show: boolean;
  onClose: () => void;
}> = ({ show, onClose }) => {
  const [minutes, setMinutes] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isBeeping, setIsBeeping] = useState(false);
  const [timerScale, setTimerScale] = useState(1);
  const [timerPos, setTimerPos] = useState({ x: 40, y: 80 });

  const audioRef = useRef<HTMLAudioElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hasInitializedTimerPos = useRef(false);

  // Initialize timer position to center when first shown
  useEffect(() => {
    if (show && !hasInitializedTimerPos.current) {
      const centerX = window.innerWidth / 2 - 150;
      const centerY = window.innerHeight / 2 - 150;
      setTimerPos({ x: centerX, y: centerY });
      hasInitializedTimerPos.current = true;
    }
  }, [show]);

  // 初始化音效
  useEffect(() => {
    const audio = new Audio(
      'https://storage.googleapis.com/duotopia-social-media-videos/website/sounds/timerring.mp3'
    );
    audio.loop = true;
    audioRef.current = audio;
    return () => {
      audio.pause();
      audio.src = '';
    };
  }, []);

  const stopBeeping = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsBeeping(false);
  }, []);

  const startBeeping = useCallback(() => {
    setIsBeeping(true);
    if (audioRef.current) {
      audioRef.current.play().catch((e) => console.log('Audio play prevented:', e));
    }
  }, []);

  // 計時邏輯
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    } else if (timeLeft === 0 && isActive) {
      setIsActive(false);
      startBeeping();
      clearInterval(interval!);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, timeLeft, startBeeping]);

  const currentMin = isActive
    ? Math.floor(timeLeft / 60)
    : timeLeft > 0
      ? Math.floor(timeLeft / 60)
      : minutes;
  const currentSec = isActive
    ? timeLeft % 60
    : timeLeft > 0
      ? timeLeft % 60
      : seconds;

  // 時鐘刻度
  const ticksElement = useMemo(() => {
    const ticks = [];
    for (let i = 0; i < 60; i++) {
      const isMajor = i % 5 === 0;
      ticks.push(
        <div
          key={i}
          className={`absolute ${isMajor ? 'bg-gray-800' : 'bg-gray-400'}`}
          style={{
            width: isMajor ? '3px' : '1px',
            height: isMajor ? '14px' : '7px',
            left: '50%',
            top: '50%',
            transformOrigin: `50% 120px`,
            transform: `translate(-50%, -120px) rotate(${i * 6}deg)`,
          }}
        />
      );
    }
    return ticks;
  }, []);

  const startDrag = (
    e: React.MouseEvent | React.TouchEvent,
    setPos: (pos: { x: number; y: number }) => void,
    currentPos: { x: number; y: number }
  ) => {
    if (
      (e.target as HTMLElement).closest('button') ||
      (e.target as HTMLElement).closest('.resize-handle') ||
      (e.target as HTMLElement).closest('.settings-panel')
    ) {
      return;
    }

    const clientX = (e as React.TouchEvent).touches
      ? (e as React.TouchEvent).touches[0].clientX
      : (e as React.MouseEvent).clientX;
    const clientY = (e as React.TouchEvent).touches
      ? (e as React.TouchEvent).touches[0].clientY
      : (e as React.MouseEvent).clientY;

    const startX = clientX - currentPos.x;
    const startY = clientY - currentPos.y;
    let frameId: number | null = null;

    const onMove = (moveEvent: MouseEvent | TouchEvent) => {
      const moveX = (moveEvent as TouchEvent).touches
        ? (moveEvent as TouchEvent).touches[0].clientX
        : (moveEvent as MouseEvent).clientX;
      const moveY = (moveEvent as TouchEvent).touches
        ? (moveEvent as TouchEvent).touches[0].clientY
        : (moveEvent as MouseEvent).clientY;

      if (frameId) cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(() => {
        setPos({ x: moveX - startX, y: moveY - startY });
      });

      if ((moveEvent as TouchEvent).touches) moveEvent.preventDefault();
    };

    const onEnd = () => {
      if (frameId) cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onEnd);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onEnd);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
  };

  const startResize = (
    e: React.MouseEvent | React.TouchEvent,
    setScale: (scale: number) => void,
    currentScale: number
  ) => {
    e.stopPropagation();
    const clientX = (e as React.TouchEvent).touches
      ? (e as React.TouchEvent).touches[0].clientX
      : (e as React.MouseEvent).clientX;
    const startX = clientX;
    const startScale = currentScale;
    let frameId: number | null = null;

    const onMove = (moveEvent: MouseEvent | TouchEvent) => {
      const moveX = (moveEvent as TouchEvent).touches
        ? (moveEvent as TouchEvent).touches[0].clientX
        : (moveEvent as MouseEvent).clientX;
      const delta = (moveX - startX) * 0.005;

      if (frameId) cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(() => {
        setScale(Math.max(0.5, Math.min(2.0, startScale + delta)));
      });

      if ((moveEvent as TouchEvent).touches) moveEvent.preventDefault();
    };

    const onEnd = () => {
      if (frameId) cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onEnd);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onEnd);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
  };

  if (!show) return null;

  return (
    <div
      className="fixed flex flex-col items-center group z-[200]"
      ref={containerRef}
      style={{
        width: '320px',
        left: `${timerPos.x}px`,
        top: `${timerPos.y}px`,
        transform: `scale(${timerScale})`,
        transformOrigin: 'top left',
      }}
      onMouseDown={(e) => startDrag(e, setTimerPos, timerPos)}
      onTouchStart={(e) => startDrag(e, setTimerPos, timerPos)}
    >
      <div className="w-full flex justify-between items-center px-6 py-1 opacity-0 group-hover:opacity-100">
        <GripHorizontal size={18} className="text-gray-400" />
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-red-500"
          aria-label="Close timer"
        >
          <X size={18} />
        </button>
      </div>

      <div
        className={`relative flex items-center justify-center w-[260px] h-[260px] rounded-full bg-white/70 backdrop-blur-md border-[6px] border-white/80 shadow-2xl transition-all ${
          isBeeping ? 'animate-pulse ring-8 ring-blue-400' : ''
        }`}
      >
        {ticksElement}
        <div className="relative flex flex-col items-center z-10" onMouseDown={(e) => e.stopPropagation()}>
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => {
                if (isBeeping) stopBeeping();
                if (!isActive && (minutes > 0 || seconds > 0 || timeLeft > 0)) {
                  if (timeLeft === 0) setTimeLeft(minutes * 60 + seconds);
                  setIsActive(true);
                }
              }}
              disabled={isActive}
              className={`rounded-full shadow-lg w-10 h-10 flex items-center justify-center ${
                isActive
                  ? 'bg-gray-100 text-gray-300'
                  : 'bg-green-500 text-white hover:scale-105 transition-transform'
              }`}
              aria-label="Start timer"
            >
              <Play size={18} fill="currentColor" />
            </button>
            <button
              onClick={() => {
                stopBeeping();
                setIsActive(false);
                setTimeLeft(0);
                setMinutes(0);
                setSeconds(0);
              }}
              className="rounded-full bg-red-500 text-white shadow-lg w-10 h-10 flex items-center justify-center hover:scale-105 transition-transform"
              aria-label="Stop timer"
            >
              <Square size={16} fill="currentColor" />
            </button>
          </div>

          <div className="flex items-center gap-1 text-gray-900 font-mono font-black text-5xl">
            <div className="flex flex-col items-center">
              <button
                onClick={() => {
                  if (!isActive)
                    setTimeLeft(Math.max(0, (timeLeft > 0 ? timeLeft : minutes * 60) + 60));
                }}
                className="text-gray-400 hover:text-blue-500"
                aria-label="Increase minutes"
              >
                <Triangle size={12} className="fill-current" />
              </button>
              <span>{String(currentMin).padStart(2, '0')}</span>
              <button
                onClick={() => {
                  if (!isActive)
                    setTimeLeft(Math.max(0, (timeLeft > 0 ? timeLeft : minutes * 60) - 60));
                }}
                className="text-gray-400 hover:text-blue-500 rotate-180"
                aria-label="Decrease minutes"
              >
                <Triangle size={12} className="fill-current" />
              </button>
            </div>
            <span className="text-blue-500/30">:</span>
            <div className="flex flex-col items-center">
              <button
                onClick={() => {
                  if (!isActive)
                    setTimeLeft(Math.max(0, (timeLeft > 0 ? timeLeft : minutes * 60) + 10));
                }}
                className="text-gray-400 hover:text-blue-500"
                aria-label="Increase seconds"
              >
                <Triangle size={12} className="fill-current" />
              </button>
              <span>{String(currentSec).padStart(2, '0')}</span>
              <button
                onClick={() => {
                  if (!isActive)
                    setTimeLeft(Math.max(0, (timeLeft > 0 ? timeLeft : minutes * 60) - 10));
                }}
                className="text-gray-400 hover:text-blue-500 rotate-180"
                aria-label="Decrease seconds"
              >
                <Triangle size={12} className="fill-current" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div
        className="flex gap-4 mt-4 bg-white/50 backdrop-blur-sm px-4 py-2 rounded-full border border-white/50 shadow-sm"
        onMouseDown={(e) => e.stopPropagation()}
      >
        {[1, 3, 5, 10].map((m) => (
          <button
            key={m}
            onClick={() => {
              if (!isActive) {
                setMinutes(m);
                setSeconds(0);
                setTimeLeft(m * 60);
              }
            }}
            className="text-sm font-bold text-gray-500 hover:text-blue-500 transition-colors"
          >
            {m}m
          </button>
        ))}
      </div>

      <div className="absolute inset-0 pointer-events-none transition-opacity">
        <div
          className="resize-handle pointer-events-auto absolute -right-2 -bottom-2 w-2.5 h-2.5 bg-blue-500 hover:bg-blue-600 rounded-full border border-white shadow-lg cursor-nwse-resize transition-all"
          onMouseDown={(e) => startResize(e, setTimerScale, timerScale)}
          onTouchStart={(e) => startResize(e, setTimerScale, timerScale)}
        />
      </div>
    </div>
  );
};

// Dice Component
const DiceTool: React.FC<{ show: boolean; onClose: () => void }> = ({ show, onClose }) => {
  const [diceValue, setDiceValue] = useState(1);
  const [isRolling, setIsRolling] = useState(false);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const [enableTransition, setEnableTransition] = useState(true);
  const [diceScale, setDiceScale] = useState(1);
  const [dicePos, setDicePos] = useState<{ x: number; y: number } | null>(null);

  const rollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const hasInitializedDicePos = useRef(false);

  useEffect(() => {
    if (show && !hasInitializedDicePos.current) {
      const centerX = window.innerWidth / 2 - 75;
      const centerY = window.innerHeight / 2 - 75;
      setDicePos({ x: centerX, y: centerY });
      hasInitializedDicePos.current = true;
    }
  }, [show]);

  const rollDice = () => {
    // Prevent overlapping rolls
    if (isRolling) return;
    
    // Clear any pending timeouts
    if (rollTimerRef.current) clearTimeout(rollTimerRef.current);
    
    setIsRolling(true);
    const newValue = Math.floor(Math.random() * 6) + 1;
    const targetRotations: Record<
      number,
      { x: number; y: number }
    > = {
      1: { x: 0, y: 0 },
      2: { x: 0, y: 180 },
      3: { x: 0, y: -90 },
      4: { x: 0, y: 90 },
      5: { x: -90, y: 0 },
      6: { x: 90, y: 0 },
    };
    
    // Enable transition for animation
    setEnableTransition(true);
    
    // Set rotation with 1440 offset for smooth rolling animation
    setRotation({
      x: targetRotations[newValue].x + 1440,
      y: targetRotations[newValue].y + 1440,
    });
    
    // Wait for CSS animation to complete (700ms)
    rollTimerRef.current = setTimeout(() => {
      setDiceValue(newValue);
      setIsRolling(false);
      
      // Disable transition temporarily to reset rotation without animation
      setEnableTransition(false);
      
      // Reset rotation to target value for next roll
      requestAnimationFrame(() => {
        setRotation({
          x: targetRotations[newValue].x,
          y: targetRotations[newValue].y,
        });
      });
    }, 700);
  };

  const DieFace: React.FC<{
    dots: number;
    transform: string;
    isRed?: boolean;
  }> = ({ dots, transform, isRed = false }) => {
    const dotMap: Record<number, Array<[number, number]>> = {
      1: [[50, 50]],
      2: [
        [25, 25],
        [75, 75],
      ],
      3: [
        [25, 25],
        [50, 50],
        [75, 75],
      ],
      4: [
        [25, 25],
        [25, 75],
        [75, 25],
        [75, 75],
      ],
      5: [
        [25, 25],
        [25, 75],
        [50, 50],
        [75, 25],
        [75, 75],
      ],
      6: [
        [25, 20],
        [25, 50],
        [25, 80],
        [75, 20],
        [75, 50],
        [75, 80],
      ],
    };

    return (
      <div
        className="absolute w-full h-full bg-white border border-gray-200 rounded-2xl flex items-center justify-center shadow-inner"
        style={{ transform, backfaceVisibility: 'hidden' }}
      >
        <svg width="100%" height="100%" viewBox="0 0 100 100">
          {(dotMap[dots] || []).map(([cx, cy], i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={dots === 1 ? 12 : 8}
              fill={isRed ? '#ef4444' : '#374151'}
            />
          ))}
        </svg>
      </div>
    );
  };

  const startDrag = (
    e: React.MouseEvent | React.TouchEvent,
    setPos: (pos: { x: number; y: number }) => void,
    currentPos: { x: number; y: number }
  ) => {
    if (
      (e.target as HTMLElement).closest('button') ||
      (e.target as HTMLElement).closest('.resize-handle') ||
      (e.target as HTMLElement).closest('.dice-clickable')
    ) {
      return;
    }

    const clientX = (e as React.TouchEvent).touches
      ? (e as React.TouchEvent).touches[0].clientX
      : (e as React.MouseEvent).clientX;
    const clientY = (e as React.TouchEvent).touches
      ? (e as React.TouchEvent).touches[0].clientY
      : (e as React.MouseEvent).clientY;

    const startX = clientX - currentPos.x;
    const startY = clientY - currentPos.y;
    let frameId: number | null = null;

    const onMove = (moveEvent: MouseEvent | TouchEvent) => {
      const moveX = (moveEvent as TouchEvent).touches
        ? (moveEvent as TouchEvent).touches[0].clientX
        : (moveEvent as MouseEvent).clientX;
      const moveY = (moveEvent as TouchEvent).touches
        ? (moveEvent as TouchEvent).touches[0].clientY
        : (moveEvent as MouseEvent).clientY;

      if (frameId) cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(() => {
        setPos({ x: moveX - startX, y: moveY - startY });
      });

      if ((moveEvent as TouchEvent).touches) moveEvent.preventDefault();
    };

    const onEnd = () => {
      if (frameId) cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onEnd);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onEnd);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
  };

  const startResize = (
    e: React.MouseEvent | React.TouchEvent,
    setScale: (scale: number) => void,
    currentScale: number
  ) => {
    e.stopPropagation();
    const clientX = (e as React.TouchEvent).touches
      ? (e as React.TouchEvent).touches[0].clientX
      : (e as React.MouseEvent).clientX;
    const startX = clientX;
    const startScale = currentScale;
    let frameId: number | null = null;

    const onMove = (moveEvent: MouseEvent | TouchEvent) => {
      const moveX = (moveEvent as TouchEvent).touches
        ? (moveEvent as TouchEvent).touches[0].clientX
        : (moveEvent as MouseEvent).clientX;
      const delta = (moveX - startX) * 0.005;

      if (frameId) cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(() => {
        setScale(Math.max(0.5, Math.min(2.0, startScale + delta)));
      });

      if ((moveEvent as TouchEvent).touches) moveEvent.preventDefault();
    };

    const onEnd = () => {
      if (frameId) cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onEnd);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onEnd);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
  };

  if (!show || !dicePos) return null;

  return (
    <div
      className="fixed flex flex-col items-center group z-[200]"
      style={{
        width: '150px',
        left: `${dicePos.x}px`,
        top: `${dicePos.y}px`,
        transform: `scale(${diceScale})`,
        transformOrigin: 'top left',
      }}
      onMouseDown={(e) => startDrag(e, setDicePos, dicePos)}
      onTouchStart={(e) => startDrag(e, setDicePos, dicePos)}
    >
      <div className="absolute inset-0 pointer-events-none transition-opacity">
        <div
          className="resize-handle pointer-events-auto absolute -right-2 -bottom-2 w-2.5 h-2.5 bg-indigo-500 hover:bg-indigo-600 rounded-full border border-white shadow-lg cursor-nwse-resize transition-all"
          onMouseDown={(e) => startResize(e, setDiceScale, diceScale)}
          onTouchStart={(e) => startResize(e, setDiceScale, diceScale)}
        />
      </div>
      <div className="w-full flex justify-between items-center px-4 py-1 opacity-0 group-hover:opacity-100">
        <GripHorizontal size={18} className="text-gray-400" />
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-red-500"
          aria-label="Close dice"
        >
          <X size={18} />
        </button>
      </div>

      <div
        className="dice-clickable w-20 h-20 mt-4 cursor-pointer drop-shadow-2xl"
        style={{ perspective: '800px' }}
        onClick={(e) => {
          e.stopPropagation();
          rollDice();
        }}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div
          className={`relative w-full h-full ${enableTransition ? 'transition-transform duration-700 ease-out' : ''}`}
          style={{
            transformStyle: 'preserve-3d',
            transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
          }}
        >
          <DieFace dots={1} transform="translateZ(40px)" isRed={true} />
          <DieFace dots={2} transform="rotateY(180deg) translateZ(40px)" />
          <DieFace dots={3} transform="rotateY(90deg) translateZ(40px)" />
          <DieFace dots={4} transform="rotateY(-90deg) translateZ(40px)" />
          <DieFace dots={5} transform="rotateX(90deg) translateZ(40px)" />
          <DieFace dots={6} transform="rotateX(-90deg) translateZ(40px)" />
        </div>
      </div>
    </div>
  );
};

interface DrawingCanvasProps {
  onToggleTimer: () => void;
  onToggleDice: () => void;
  isTimerOpen: boolean;
  isDiceOpen: boolean;
}

// Drawing Canvas Component
const DrawingCanvas: React.FC<DrawingCanvasProps> = ({
  onToggleTimer,
  onToggleDice,
  isTimerOpen,
  isDiceOpen,
}) => {
  const { t } = useTranslation();
  const [drawMode, setDrawMode] = useState<'pencil' | 'eraser' | null>(null);
  const [pencilColor, setPencilColor] = useState('#ef4444');
  const [pencilWidth, setPencilWidth] = useState(3);
  const [eraserWidth, setEraserWidth] = useState(20);
  const [showPencilSettings, setShowPencilSettings] = useState(false);
  const [showEraserSettings, setShowEraserSettings] = useState(false);

  const previousModeBeforePalm = useRef<'pencil' | 'eraser' | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDrawing = useRef(false);
  const isInitialized = useRef(false);

  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      console.warn('initCanvas(): canvas ref is null');
      return;
    }
    
    // Only initialize once to preserve drawings
    if (isInitialized.current) {
      console.log('initCanvas(): already initialized, skipping');
      return;
    }
    
    const width = window.innerWidth;
    const height = Math.max(window.innerHeight, document.documentElement.scrollHeight || 0);
    console.log('initCanvas(): setting canvas dimensions to', width, 'x', height);
    canvas.width = width * 2;
    canvas.height = height * 2;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    
    const context = canvas.getContext('2d');
    if (context) {
      context.scale(2, 2);
      context.lineCap = 'round';
      context.lineJoin = 'round';
      contextRef.current = context;
      isInitialized.current = true;
      console.log('initCanvas(): canvas initialized successfully');
    } else {
      console.error('initCanvas(): failed to get canvas context');
    }
  }, []);

  useEffect(() => {
    initCanvas();
  }, [initCanvas]);

  const getCoordinates = (e: MouseEvent | TouchEvent): { x: number; y: number } => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientX : (e as MouseEvent).clientX;
    const clientY = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientY : (e as MouseEvent).clientY;
    return { x: clientX - rect.left, y: clientY - rect.top };
  };

  const startDrawing = (e: React.MouseEvent | React.TouchEvent) => {
    console.log('startDrawing() called, drawMode:', drawMode);
    let currentMode = drawMode;
    if ((e as React.TouchEvent).touches && (e as React.TouchEvent).touches.length > 0) {
      const touch = (e as React.TouchEvent).touches[0];
      const isPalm =
        (e as React.TouchEvent).touches.length > 1 ||
        (touch.radiusX && touch.radiusX > 15);
      if (isPalm) {
        if (drawMode !== 'eraser') {
          previousModeBeforePalm.current = drawMode;
          setDrawMode('eraser');
          currentMode = 'eraser';
        }
      }
    }
    if (!currentMode) {
      console.warn('startDrawing(): currentMode is null, returning');
      return;
    }
    const { x, y } = getCoordinates(
      e as unknown as MouseEvent | TouchEvent
    );
    console.log('startDrawing(): x=', x, 'y=', y, 'contextRef:', contextRef.current ? 'set' : 'null', 'currentMode:', currentMode);
    if (contextRef.current) {
      contextRef.current.beginPath();
      contextRef.current.moveTo(x, y);
      if (currentMode === 'pencil') {
        contextRef.current.globalCompositeOperation = 'source-over';
        contextRef.current.strokeStyle = pencilColor;
        contextRef.current.lineWidth = pencilWidth;
        console.log('startDrawing(): pencil mode, color=', pencilColor, 'width=', pencilWidth);
      } else {
        contextRef.current.globalCompositeOperation = 'destination-out';
        contextRef.current.lineWidth = eraserWidth * 2.5;
      }
    }
    isDrawing.current = true;
    console.log('startDrawing(): isDrawing set to true');
  };

  const draw = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawing.current) return;
    if ((e as React.TouchEvent).touches && (e as React.TouchEvent).touches.length > 0) {
      const touch = (e as React.TouchEvent).touches[0];
      const isPalm =
        (e as React.TouchEvent).touches.length > 1 ||
        (touch.radiusX && touch.radiusX > 15);
      if (isPalm && drawMode !== 'eraser') {
        previousModeBeforePalm.current = drawMode;
        setDrawMode('eraser');
        if (contextRef.current) {
          contextRef.current.globalCompositeOperation = 'destination-out';
          contextRef.current.lineWidth = eraserWidth * 2.5;
        }
      }
    }
    if (!drawMode) {
      console.warn('draw(): drawMode is', drawMode, 'isDrawing:', isDrawing.current);
      return;
    }
    const { x, y } = getCoordinates(
      e as unknown as MouseEvent | TouchEvent
    );
    console.log('draw(): x=', x, 'y=', y, 'contextRef:', contextRef.current ? 'set' : 'null');
    if (contextRef.current) {
      contextRef.current.lineTo(x, y);
      contextRef.current.stroke();
      console.log('draw(): stroke called');
    }
    if ((e as React.TouchEvent).touches) e.preventDefault();
  };

  const stopDrawing = () => {
    if (!isDrawing.current) return;
    if (contextRef.current) {
      contextRef.current.closePath();
    }
    isDrawing.current = false;
    if (previousModeBeforePalm.current !== null) {
      setDrawMode(previousModeBeforePalm.current);
      previousModeBeforePalm.current = null;
    }
  };

  const colors = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#000000', '#8b5cf6', '#ec4899', '#64748b'];

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <canvas
        ref={canvasRef}
        className={`absolute top-0 left-0 z-10 ${
          drawMode ? 'cursor-crosshair touch-none pointer-events-auto' : 'pointer-events-none'
        }`}
        onMouseDown={startDrawing}
        onMouseMove={draw}
        onMouseUp={stopDrawing}
        onMouseOut={stopDrawing}
        onTouchStart={startDrawing}
        onTouchMove={draw}
        onTouchEnd={stopDrawing}
      />

      {/* 側邊工具列 */}
      <div className="fixed right-4 top-1/2 -translate-y-1/2 flex flex-col gap-1 bg-white/90 backdrop-blur-md shadow-2xl border border-gray-200 rounded-l-xl p-1.5 z-[150] pointer-events-auto">
        <button
          onClick={onToggleTimer}
          className={`p-1.5 rounded-lg transition-all duration-300 ${
            isTimerOpen
              ? 'bg-blue-500 text-white shadow-md'
              : 'hover:bg-gray-100 text-blue-500'
          }`}
          aria-label="Timer"
        >
          <Timer size={16} />
        </button>

        <button
          onClick={onToggleDice}
          className={`p-1.5 rounded-lg transition-all duration-300 ${
            isDiceOpen
              ? 'bg-gray-800 text-white shadow-md'
              : 'hover:bg-gray-100 text-gray-600'
          }`}
          aria-label="Dice"
        >
          <Dice5 size={16} />
        </button>

        <div className="w-full h-px bg-gray-200 my-1" />

        <div className="relative">
          <button
            onClick={() => setDrawMode(drawMode === 'pencil' ? null : 'pencil')}
            onDoubleClick={() => {
              setDrawMode('pencil');
              setShowPencilSettings(true);
            }}
            className={`p-1.5 rounded-lg transition-all duration-300 ${
              drawMode === 'pencil'
                ? 'bg-red-500 text-white shadow-md'
                : 'hover:bg-gray-100 text-red-500'
            }`}
            aria-label="Pencil"
          >
            <Pencil size={16} />
          </button>
          {showPencilSettings && (
            <div className="settings-panel absolute right-full mr-2 top-0 bg-white shadow-xl border border-gray-200 rounded-xl p-3 flex flex-col gap-3 min-w-[120px]">
              <div className="flex justify-between items-center text-[10px] font-bold text-gray-400">
                <span>{t('teachingTools.pencil.settings')}</span>
                <button onClick={() => setShowPencilSettings(false)}>
                  <X size={12} />
                </button>
              </div>
              <div className="grid grid-cols-4 gap-1">
                {colors.map((c) => (
                  <button
                    key={c}
                    onClick={() => setPencilColor(c)}
                    className={`w-5 h-5 rounded-full border ${
                      pencilColor === c ? 'ring-2 ring-offset-1 ring-gray-400' : 'border-gray-200'
                    }`}
                    style={{ backgroundColor: c }}
                    aria-label={`Color ${c}`}
                  />
                ))}
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-gray-500">{t('teachingTools.pencil.thicknessValue', { value: pencilWidth })}</span>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={pencilWidth}
                  onChange={(e) => setPencilWidth(parseInt(e.target.value))}
                  className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-red-500"
                />
              </div>
            </div>
          )}
        </div>

        <div className="relative">
          <button
            onClick={() => setDrawMode(drawMode === 'eraser' ? null : 'eraser')}
            onDoubleClick={() => {
              setDrawMode('eraser');
              setShowEraserSettings(true);
            }}
            className={`p-1.5 rounded-lg transition-all duration-300 ${
              drawMode === 'eraser'
                ? 'bg-blue-600 text-white shadow-md'
                : 'hover:bg-gray-100 text-blue-600'
            }`}
            aria-label="Eraser"
          >
            <Eraser size={16} />
          </button>
          {showEraserSettings && (
            <div className="settings-panel absolute right-full mr-2 top-0 bg-white shadow-xl border border-gray-200 rounded-xl p-3 flex flex-col gap-3 min-w-[120px]">
              <div className="flex justify-between items-center text-[10px] font-bold text-gray-400">
                <span>{t('teachingTools.eraser.settings')}</span>
                <button onClick={() => setShowEraserSettings(false)}>
                  <X size={12} />
                </button>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-gray-500">{t('teachingTools.eraser.sizeValue', { value: eraserWidth })}</span>
                <input
                  type="range"
                  min="5"
                  max="100"
                  value={eraserWidth}
                  onChange={(e) => setEraserWidth(parseInt(e.target.value))}
                  className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
              <button
                onClick={() => {
                  if (canvasRef.current && contextRef.current) {
                    contextRef.current.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
                    setShowEraserSettings(false);
                  }
                }}
                className="text-[10px] bg-gray-100 hover:bg-red-50 py-1 rounded text-red-500 font-bold border border-red-100"
              >
                {t('teachingTools.eraser.clearCanvas')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main Toolbar Component
const DigitalTeachingToolbar: React.FC = () => {
  const [showTimer, setShowTimer] = useState(false);
  const [showDice, setShowDice] = useState(false);

  const handleToggleTimer = () => {
    setShowTimer((prev) => !prev);
  };

  const handleToggleDice = () => {
    setShowDice((prev) => !prev);
  };

  return (
    <div className="fixed inset-0 pointer-events-none z-[140]">
      <div className="relative w-full h-full">
        <DrawingCanvas
          onToggleTimer={handleToggleTimer}
          onToggleDice={handleToggleDice}
          isTimerOpen={showTimer}
          isDiceOpen={showDice}
        />
      </div>

      <div className="pointer-events-auto">
        <TimerTool
          show={showTimer}
          onClose={() => setShowTimer(false)}
        />
      </div>
      <div className="pointer-events-auto">
        <DiceTool
          show={showDice}
          onClose={() => setShowDice(false)}
        />
      </div>
    </div>
  );
};

export default DigitalTeachingToolbar;
