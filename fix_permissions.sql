-- Force Enable RLS
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Drop existing delete policy if it exists to avoid conflicts
DROP POLICY IF EXISTS "Users can delete their own projects" ON public.projects;

-- Re-create the DELETE policy clearly
CREATE POLICY "Users can delete their own projects"
ON public.projects FOR DELETE
USING (auth.uid() = user_id);

-- Verify other policies exist just in case
DROP POLICY IF EXISTS "Users can view their own projects" ON public.projects;
CREATE POLICY "Users can view their own projects" ON public.projects FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own projects" ON public.projects;
CREATE POLICY "Users can insert their own projects" ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own projects" ON public.projects;
CREATE POLICY "Users can update their own projects" ON public.projects FOR UPDATE USING (auth.uid() = user_id);
