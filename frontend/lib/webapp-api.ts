import axios from "axios";

const BOT_INTERNAL_TOKEN = process.env.NEXT_PUBLIC_BOT_INTERNAL_TOKEN || "secret_bot_internal_token_change_me_in_production";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api",
});

api.interceptors.request.use((config) => {
  // Use Bot Internal Token instead of JWT for webapp
  config.headers["X-Bot-Token"] = BOT_INTERNAL_TOKEN;
  return config;
});

// Types
export interface WebappUserData {
  id: number;
  full_name: string;
  role: string;
  phone: string;
  groups: Array<{ id: number; name: string }>;
  is_admin: boolean;
}

export interface Group {
  id: number;
  name: string;
  schedule_time: string | null;
  student_count?: number;
}

export interface Stats {
  today_homework_submitted: number;
  today_homework_not_submitted: number;
  today_payment_received: number;
  total_students: number;
}

// API Functions
export async function getWebappData(telegramId: number): Promise<WebappUserData> {
  const response = await api.get("/bot/webapp-data", {
    params: { telegram_id: telegramId }
  });
  return response.data.data;
}

export async function getGroups(): Promise<Group[]> {
  const response = await api.get("/bot/groups-for-admin");
  return response.data.data;
}

export async function getUsersByGroup(groupId: number): Promise<Array<{
  id: number;
  full_name: string;
  phone: string;
  telegram_id: number | null;
  has_telegram: boolean;
}>> {
  const response = await api.get("/bot/users-by-group", {
    params: { group_id: groupId }
  });
  return response.data.data;
}

export async function sendNotification(data: {
  sent_by: number;
  target_type: "all" | "group" | "user";
  target_id?: number;
  title: string;
  body: string;
  notification_type: string;
}) {
  const response = await api.post("/bot/send-notification", data);
  return response.data;
}

export async function createHomework(data: {
  sent_by: number;
  title: string;
  description: string;
  due_date: string;
  group_id: number;
  lesson_id?: number;
}) {
  const response = await api.post("/bot/homework/create", data);
  return response.data;
}

export async function getStats(): Promise<Stats> {
  const response = await api.get("/bot/stats");
  return response.data.data;
}

export default api;
