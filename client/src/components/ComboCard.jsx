import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ChevronDown } from 'lucide-react';
import { TiltCard } from './TiltCard';

/** Colour the score badge from red (low) through gold to green (high). */
function scoreColor(score) {
  if (score >= 8) return '#5bbf7a';
  if (score >= 6) return '#c8a15a';
  if (score >= 4) return '#d89a4a';
  return '#c86a5a';
}

/**
 * One ranked outfit combo. `combo.items` reference the uploaded garments by
 * category+index; `previews` maps "category:index" -> object URL for thumbnails.
 */
export function ComboCard({ combo, previews, rank }) {
  const [open, setOpen] = useState(false);
  const color = scoreColor(combo.aesthetic_score);

  return (
    <TiltCard className="p-5">
      <div style={{ transform: 'translateZ(40px)' }} className="flex flex-col gap-4">
        <div className="flex items-start justify-between">
          <span className="font-display text-sm text-muted">#{rank}</span>
          <div
            className="flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold"
            style={{ background: `${color}22`, color }}
          >
            <Sparkles size={14} />
            {combo.aesthetic_score}/10
          </div>
        </div>

        {/* garment stack */}
        <div className="flex gap-2">
          {combo.items.map((item) => {
            const src = previews[`${item.category}:${item.index}`];
            return (
              <div key={`${item.category}:${item.index}`} className="flex-1">
                <div className="aspect-[3/4] overflow-hidden rounded-xl bg-elevated">
                  {src && <img src={src} alt={item.category} className="h-full w-full object-cover" />}
                </div>
                <p className="mt-1 text-center text-[10px] uppercase tracking-widest text-muted">
                  {item.category}
                </p>
              </div>
            );
          })}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {combo.vibe_tags.map((tag) => (
            <span key={tag} className="rounded-full bg-white/[0.06] px-2.5 py-0.5 text-xs text-white/80">
              {tag}
            </span>
          ))}
        </div>

        {combo.why && <p className="text-sm leading-relaxed text-muted">{combo.why}</p>}

        {combo.inspiration?.length > 0 && (
          <div>
            <button
              onClick={() => setOpen((o) => !o)}
              className="flex w-full items-center justify-between text-sm text-accent"
            >
              <span>Recreate this look · {combo.inspiration.length} refs</span>
              <ChevronDown
                size={16}
                className={`transition-transform ${open ? 'rotate-180' : ''}`}
              />
            </button>
            <AnimatePresence>
              {open && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {combo.inspiration.map((pic, i) => (
                      <a
                        key={i}
                        href={pic.url}
                        target="_blank"
                        rel="noreferrer"
                        className="aspect-[3/4] overflow-hidden rounded-lg"
                      >
                        <img
                          src={pic.image_url}
                          alt={pic.title || 'inspiration'}
                          className="h-full w-full object-cover transition-transform hover:scale-105"
                        />
                      </a>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </TiltCard>
  );
}
