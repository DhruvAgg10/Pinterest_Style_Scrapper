import { useMemo, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Wand2, Shirt, Loader2 } from 'lucide-react';
import { UploadZone } from '../components/UploadZone';
import { ComboCard } from '../components/ComboCard';
import { Button } from '../components/ui/Button';

const CATEGORIES = [
  { key: 'upper', label: 'Tops', hint: 'shirts, tees, jackets', accent: '#c8a15a' },
  { key: 'lower', label: 'Bottoms', hint: 'jeans, trousers, skirts', accent: '#7a9bc8' },
  { key: 'shoes', label: 'Shoes', hint: 'sneakers, boots, heels', accent: '#b07ac8' },
];

export function ClosetStudio() {
  const [closet, setCloset] = useState({ upper: [], lower: [], shoes: [] });
  const [combos, setCombos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const setFilesFor = (key) => (updater) =>
    setCloset((prev) => ({
      ...prev,
      [key]: typeof updater === 'function' ? updater(prev[key]) : updater,
    }));

  // Stable object-URL map for combo thumbnails ("category:index" -> url).
  const previews = useMemo(() => {
    const map = {};
    for (const { key } of CATEGORIES) {
      closet[key].forEach((file, i) => {
        map[`${key}:${i}`] = URL.createObjectURL(file);
      });
    }
    return map;
  }, [closet]);

  const totalItems = CATEGORIES.reduce((n, c) => n + closet[c.key].length, 0);
  const categoriesWithItems = CATEGORIES.filter((c) => closet[c.key].length > 0).length;
  const canGenerate = categoriesWithItems >= 2 && !loading;

  const generate = async () => {
    setLoading(true);
    setError(null);
    setCombos(null);
    const form = new FormData();
    closet.upper.forEach((f) => form.append('upper_images', f));
    closet.lower.forEach((f) => form.append('lower_images', f));
    closet.shoes.forEach((f) => form.append('shoes_images', f));
    try {
      const { data } = await axios.post('/api/combos', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setCombos(data);
    } catch (e) {
      console.error(e);
      setError('Could not build combos. Try again in a moment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-5 pb-24">
      {/* hero */}
      <section className="relative py-20 text-center">
        <div className="pointer-events-none absolute inset-0 grain opacity-40" />
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 text-xs uppercase tracking-[0.3em] text-accent"
        >
          Your closet, restyled
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="font-display text-5xl leading-tight text-gradient sm:text-6xl"
        >
          Viral outfit combos
          <br />
          from clothes you own
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="mx-auto mt-5 max-w-xl text-muted"
        >
          Upload your tops, bottoms and shoes. AI pairs every combination, scores the
          aesthetic, and shows you reference photos to recreate the look.
        </motion.p>
      </section>

      {/* upload grid */}
      <section className="grid gap-6 md:grid-cols-3">
        {CATEGORIES.map((cat) => (
          <div key={cat.key} className="rounded-2xl glass p-5">
            <UploadZone
              label={cat.label}
              hint={cat.hint}
              accent={cat.accent}
              files={closet[cat.key]}
              setFiles={setFilesFor(cat.key)}
            />
          </div>
        ))}
      </section>

      {/* action bar */}
      <div className="sticky bottom-5 z-20 mt-8 flex items-center justify-between rounded-full glass px-6 py-3">
        <span className="flex items-center gap-2 text-sm text-muted">
          <Shirt size={16} />
          {totalItems} items · {categoriesWithItems}/3 categories
        </span>
        <Button onClick={generate} disabled={!canGenerate} size="lg">
          {loading ? <Loader2 className="animate-spin" size={18} /> : <Wand2 size={18} />}
          {loading ? 'Styling…' : 'Generate combos'}
        </Button>
      </div>
      {categoriesWithItems < 2 && (
        <p className="mt-3 text-center text-xs text-muted">
          Add at least two categories (e.g. tops + bottoms) to start.
        </p>
      )}

      {/* results */}
      {error && <p className="mt-10 text-center text-sm text-red-400">{error}</p>}

      {combos && (
        <section className="mt-14">
          <div className="mb-6 flex items-baseline justify-between">
            <h2 className="font-display text-3xl">Your ranked combos</h2>
            <span className="text-sm text-muted">
              {combos.scored} of {combos.total_possible} scored
            </span>
          </div>
          {combos.combos?.length ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" style={{ perspective: 1500 }}>
              {combos.combos.map((combo, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <ComboCard combo={combo} previews={previews} rank={i + 1} />
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted">{combos.message || 'No combos yet.'}</p>
          )}
        </section>
      )}
    </div>
  );
}
