import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTasks, completeTask, deleteTask } from '../api';
import { CheckCircle, Circle, Trash2, Clock, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';

const PriorityIcon = ({ priority }) => {
    // Priority: 1=LOW, 2=MED, 3=HIGH, 4=URGENT
    if (priority === 4) return <AlertCircle className="text-red-500" size={20} />;
    if (priority === 3) return <AlertCircle className="text-orange-500" size={20} />;
    if (priority === 2) return <Clock className="text-blue-400" size={20} />;
    return <Circle className="text-gray-400" size={20} />;
};

const TaskList = () => {
    const queryClient = useQueryClient();
    const { data: tasks, isLoading, error } = useQuery({
        queryKey: ['tasks'],
        queryFn: () => getTasks(),
    });

    const completeMutation = useMutation({
        mutationFn: completeTask,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: deleteTask,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });

    if (isLoading) return <div className="text-center p-8 text-gray-400">Loading tasks...</div>;
    if (error) return <div className="text-center p-8 text-red-500">Error loading tasks: {error.message}</div>;

    return (
        <div className="space-y-4">
            <AnimatePresence>
                {tasks.map((task) => (
                    <motion.div
                        key={task.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, height: 0 }}
                        className={`p-4 rounded-lg border border-gray-700 flex items-center gap-4 ${task.status === 'completed' ? 'bg-opacity-50 bg-gray-800' : 'bg-surface'
                            }`}
                    >
                        <button
                            onClick={() => completeMutation.mutate(task.id)}
                            disabled={task.status === 'completed'}
                            className="text-gray-400 hover:text-green-500 transition-colors"
                        >
                            {task.status === 'completed' ? (
                                <CheckCircle className="text-green-500" size={24} />
                            ) : (
                                <Circle size={24} />
                            )}
                        </button>

                        <div className="flex-1">
                            <h3 className={`text-lg font-medium ${task.status === 'completed' ? 'line-through text-gray-500' : 'text-white'}`}>
                                {task.title}
                            </h3>
                            {task.description && (
                                <p className="text-sm text-gray-400">{task.description}</p>
                            )}
                            <div className="flex gap-2 text-xs text-gray-500 mt-1">
                                {task.category && <span className="bg-gray-700 px-2 py-0.5 rounded">{task.category}</span>}
                                {task.due_date && <span>Due: {task.due_date}</span>}
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <PriorityIcon priority={task.priority} />
                            <button
                                onClick={() => deleteMutation.mutate(task.id)}
                                className="text-gray-500 hover:text-red-500 transition-colors"
                            >
                                <Trash2 size={20} />
                            </button>
                        </div>
                    </motion.div>
                ))}
            </AnimatePresence>
            {tasks.length === 0 && (
                <div className="text-center py-10 text-gray-500">
                    No tasks found. Add one above!
                </div>
            )}
        </div>
    );
};

export default TaskList;
