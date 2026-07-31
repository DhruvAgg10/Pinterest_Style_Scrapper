import { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, MapPin, Loader2 } from 'lucide-react';
import { TiltCard } from './TiltCard';

const LOCATIONS = [
  'cafe', 'street style', 'beach', 'rooftop', 'city night',
  'mountains', 'park', 'urban', 'studio',
];

function scoreColor(score) {
  if (score >= 8) return '#5bbf7a';
  if (score >= 6) return '#c8a15a';
  if (score >= 4) return '#d89a4a';
  return '#c86a5a';
}

/**
 * One ranked outfit combo. Pick a location and the card fetches reference photos
 * of a person wearing this outfit in that setting (via /api/looks).
 */
export function ComboCard({ combo, previews, rank }) {
  const color = scoreColor(combo.aesthetic_score);
  const [location, setLocation] = useState(null);
  const [looks, setLooks] = useState(combo.inspiration || []);
  const [loading, setLoading] = useState(false);

  const pickLocation = async (loc) => {
    setLocation(loc);
    setLoading(true);
    try {
      const { data } = await axios.get('/api/looks', {
        params: { query: combo.search_query, location: loc, limit: 8 },
      });
      setLooks(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

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

        {/* location picker */}
        <div>
          <div className="mb-2 flex items-center gap-1.5 text-xs uppercase tracking-widest text-muted">
            <MapPin size={12} /> See this outfit in
          </div>
          <div className="flex flex-wrap gap-1.5">
            {LOCATIONS.map((loc) => (
              <button
                key={loc}
                onClick={() => pickLocation(loc)}
                className={`rounded-full px-3 py-1 text-xs capitalize transition-colors ${
                  location === loc ? 'bg-accent text-ink' : 'bg-white/[0.05] text-muted hover:text-white'
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>

        {/* reference gallery */}
        <div className="min-h-[4rem]">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted">
              <Loader2 className="animate-spin" size={16} /> Finding {location} looks…
            </div>
          ) : looks.length > 0 ? (
            <>
              {location && (
                <p className="mb-2 text-xs text-accent-soft">
                  This outfit · <span className="capitalize">{location}</span>
                </p>
              )}
              <div className="grid grid-cols-2 gap-2">
                <AnimatePresence mode="popLayout">
                  {looks.map((pic, i) => (
                    <motion.a
                      key={pic.image_url + i}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      href={pic.url}
                      target="_blank"
                      rel="noreferrer"
                      className="aspect-[3/4] overflow-hidden rounded-lg"
                    >
                      <img
                        src={pic.image_url}
                        alt={pic.title || 'reference'}
                        loading="lazy"
                        className="h-full w-full object-cover transition-transform hover:scale-105"
                      />
                    </motion.a>
                  ))}
                </AnimatePresence>
              </div>
            </>
          ) : (
            <p className="py-4 text-center text-xs text-muted">Pick a location to see references.</p>
          )}
        </div>
      </div>
    </TiltCard>
  );
}
