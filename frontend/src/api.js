import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

export const getTasks = async (status, category) => {
    const params = {};
    if (status) params.status = status;
    if (category) params.category = category;
    const response = await api.get('/tasks', { params });
    return response.data;
};

export const createTask = async (task) => {
    const response = await api.post('/tasks', task);
    return response.data;
};

export const updateTask = async (taskId, updates) => {
    const response = await api.put(`/tasks/${taskId}`, updates);
    return response.data;
};

export const completeTask = async (taskId) => {
    const response = await api.post(`/tasks/${taskId}/complete`);
    return response.data;
};

export const deleteTask = async (taskId) => {
    await api.delete(`/tasks/${taskId}`);
};

export default api;
