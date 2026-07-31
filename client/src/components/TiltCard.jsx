import { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '../lib/utils';

/**
 * Aceternity-style 3D tilt card. Tracks the pointer and rotates the card in 3D
 * space with a soft spring, plus a moving glare. Children can use `translate-z`
 * via inline transform for a layered pop. Pure Framer Motion — no three.js.
 */
export function TiltCard({ className, children, glare = true }) {
  const ref = useRef(null);
  const [hovered, setHovered] = useState(false);

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [10, -10]), { stiffness: 200, damping: 20 });
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-12, 12]), { stiffness: 200, damping: 20 });
  const glareX = useTransform(x, [-0.5, 0.5], ['0%', '100%']);

  const handleMove = (e) => {
    const rect = ref.current.getBoundingClientRect();
    x.set((e.clientX - rect.left) / rect.width - 0.5);
    y.set((e.clientY - rect.top) / rect.height - 0.5);
  };
  const reset = () => {
    x.set(0);
    y.set(0);
    setHovered(false);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={reset}
      style={{ rotateX, rotateY, transformStyle: 'preserve-3d', transformPerspective: 1000 }}
      className={cn(
        'relative rounded-2xl glass shadow-card transition-shadow duration-300',
        hovered && 'shadow-glow',
        className,
      )}
    >
      {children}
      {glare && (
        <motion.div
          style={{ left: glareX }}
          className="pointer-events-none absolute inset-y-0 -ml-24 w-24 skew-x-12 bg-white/10 blur-2xl opacity-0 transition-opacity"
          animate={{ opacity: hovered ? 1 : 0 }}
        />
      )}
    </motion.div>
  );
}
