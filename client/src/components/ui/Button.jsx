import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

const variants = {
  primary:
    'bg-accent text-ink hover:bg-accent-soft shadow-glow',
  ghost:
    'bg-white/[0.04] text-white hover:bg-white/[0.08] border border-white/10',
  outline:
    'bg-transparent text-white border border-white/20 hover:border-accent/60',
};

const sizes = {
  sm: 'h-9 px-4 text-sm',
  md: 'h-11 px-6 text-sm',
  lg: 'h-13 px-8 text-base py-3.5',
};

export function Button({ variant = 'primary', size = 'md', className, children, ...props }) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-full font-medium tracking-wide transition-colors disabled:opacity-50 disabled:pointer-events-none',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </motion.button>
  );
}
