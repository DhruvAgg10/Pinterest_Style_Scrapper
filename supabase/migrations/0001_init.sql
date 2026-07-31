-- StylePilot — Supabase schema
-- Run this in the Supabase project: SQL Editor -> New query -> paste -> Run.
-- Auth users live in the built-in `auth.users` table; we reference them by id.

create table if not exists public.closet_items (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references auth.users (id) on delete cascade,
    category    text not null check (category in ('upper', 'lower', 'shoes', 'accessories', 'tattoo')),
    image_url   text not null,
    tags        text[] not null default '{}',
    colors      text[] not null default '{}',
    created_at  timestamptz not null default now()
);

create index if not exists closet_items_user_idx on public.closet_items (user_id);

-- Row Level Security: each user can only see and modify their own closet.
alter table public.closet_items enable row level security;

drop policy if exists "own closet select" on public.closet_items;
create policy "own closet select" on public.closet_items
    for select using (auth.uid() = user_id);

drop policy if exists "own closet insert" on public.closet_items;
create policy "own closet insert" on public.closet_items
    for insert with check (auth.uid() = user_id);

drop policy if exists "own closet delete" on public.closet_items;
create policy "own closet delete" on public.closet_items
    for delete using (auth.uid() = user_id);

-- Storage bucket for uploaded garment images (create once).
insert into storage.buckets (id, name, public)
values ('closet', 'closet', true)
on conflict (id) do nothing;
