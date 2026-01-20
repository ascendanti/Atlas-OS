import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TaskList from './components/TaskList';
import TaskForm from './components/TaskForm';
import { Layout } from 'lucide-react';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-white font-sans selection:bg-primary selection:text-white">
        <header className="bg-surface border-b border-gray-700 py-4 mb-8 sticky top-0 z-10 shadow-lg backdrop-blur-sm bg-opacity-80">
          <div className="container mx-auto px-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="bg-primary p-1.5 rounded-lg">
                <Layout className="text-white" size={24} />
              </div>
              <h1 className="text-2xl font-bold tracking-tight">Atlas <span className="text-primary">OS</span></h1>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 max-w-3xl">
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-200">Task Management</h2>
            <TaskForm />
            <TaskList />
          </section>
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
