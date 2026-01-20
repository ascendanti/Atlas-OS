import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createTask } from '../api';
import { Plus } from 'lucide-react';

const TaskForm = () => {
    const [title, setTitle] = useState('');
    const [priority, setPriority] = useState('medium');
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: createTask,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
            setTitle('');
            setPriority('medium');
        },
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!title.trim()) return;
        mutation.mutate({ title, priority: priority.toUpperCase() }); // API expects uppercase for Enum mapping if string
        // Actually schema expects int for priority in TaskCreate, wait.
        // Let's check schemas.py: priority: TaskPriority = TaskPriority.MEDIUM
        // TaskPriority is (int, Enum).
        // So we should send the integer value or make sure the backend handles it.
        // The backend `create_task` does: `tracker_priority = TrackerPriority(task.priority.value)`
        // Pydantic will validate `task.priority`.
        // If I send "medium", pydantic might fail if it expects int.
        // Let's check `TaskPriority` definition in schemas.py:
        // class TaskPriority(int, Enum): LOW=1, MEDIUM=2, ...
        // So it expects 1, 2, 3, 4.
    };

    // I need to correct the priority handling to send integers.
    const priorityMap = {
        low: 1,
        medium: 2,
        high: 3,
        urgent: 4
    };

    const handleCorrectSubmit = (e) => {
        e.preventDefault();
        if (!title.trim()) return;
        mutation.mutate({
            title,
            priority: priorityMap[priority]
        });
    }

    return (
        <form onSubmit={handleCorrectSubmit} className="bg-surface p-4 rounded-lg shadow-md mb-6 border border-gray-700">
            <div className="flex gap-4">
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Add a new task..."
                    className="flex-1 bg-background text-white p-2 rounded border border-gray-600 focus:border-primary focus:outline-none"
                />
                <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="bg-background text-white p-2 rounded border border-gray-600 focus:border-primary focus:outline-none"
                >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                </select>
                <button
                    type="submit"
                    disabled={mutation.isPending}
                    className="bg-primary hover:bg-blue-600 text-white p-2 rounded flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                    <Plus size={20} />
                    <span>Add</span>
                </button>
            </div>
        </form>
    );
};

export default TaskForm;
