import { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * Multi-image upload zone for one closet category. Holds File objects in the
 * parent via `files`/`setFiles`, renders thumbnail previews, supports drag-drop.
 */
export function UploadZone({ label, hint, files, setFiles, accent }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const addFiles = (list) => {
    const images = Array.from(list).filter((f) => f.type.startsWith('image/'));
    setFiles((prev) => [...prev, ...images]);
  };
  const removeAt = (index) => setFiles((prev) => prev.filter((_, i) => i !== index));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h3 className="font-display text-lg text-white">{label}</h3>
        <span className="text-xs text-muted">{files.length} item{files.length === 1 ? '' : 's'}</span>
      </div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'group relative cursor-pointer rounded-2xl border border-dashed border-line p-4 transition-colors',
          dragging ? 'border-accent bg-accent/5' : 'hover:border-white/25',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
        {files.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center text-muted">
            <span
              className="flex h-11 w-11 items-center justify-center rounded-full"
              style={{ background: `${accent}22`, color: accent }}
            >
              <Plus size={20} />
            </span>
            <p className="text-sm">Drop or click to add</p>
            {hint && <p className="text-xs text-muted/70">{hint}</p>}
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            <AnimatePresence>
              {files.map((file, index) => (
                <motion.div
                  key={`${file.name}-${index}`}
                  layout
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="relative aspect-[3/4] overflow-hidden rounded-lg"
                >
                  <img
                    src={URL.createObjectURL(file)}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeAt(index);
                    }}
                    className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black"
                  >
                    <X size={12} />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
            <div className="flex aspect-[3/4] items-center justify-center rounded-lg border border-dashed border-line text-muted group-hover:border-white/25">
              <Plus size={18} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
