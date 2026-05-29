/**
 * JobPilot — Application Types
 */

export interface Application {
  id: string;
  user_id: string;
  recruiter_id: string | null;
  resume_id: string | null;
  company_name: string;
  job_title: string;
  job_url: string | null;
  job_description_raw: string | null;
  job_description_parsed: Record<string, unknown> | null;
  status: ApplicationStatus;
  priority: Priority;
  source: string | null;
  technologies: string[] | null;
  salary_range: string | null;
  location: string | null;
  work_type: string | null;
  employment_type: string | null;
  seniority_level: string | null;
  experience_years: string | null;
  experience_summary: string | null;
  applied_date: string | null;
  deadline: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type ApplicationStatus =
  | "draft"
  | "applied"
  | "screening"
  | "interview"
  | "assessment"
  | "offer"
  | "rejected"
  | "withdrawn"
  | "accepted";

export type Priority = "high" | "medium" | "low";

export interface ApplicationListResponse {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Interview {
  id: string;
  application_id: string;
  round_type: string;
  round_number: number;
  scheduled_at: string | null;
  duration_minutes: number | null;
  location_or_link: string | null;
  interviewer_name: string | null;
  status: string;
  notes: string | null;
  feedback: string | null;
  preparation_notes: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsOverview {
  total_applications: number;
  total_interviews: number;
  total_offers: number;
  total_rejections: number;
  total_pending: number;
  response_rate: number;
  interview_conversion_rate: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
  percentage: number;
}

export interface TrendDataPoint {
  date: string;
  count: number;
}

export interface Notification {
  id: string;
  user_id: string;
  application_id: string | null;
  channel: string;
  type: string;
  title: string;
  message: string | null;
  is_read: boolean;
  is_sent: boolean;
  sent_at: string | null;
  created_at: string;
}

export interface FollowUp {
  id: string;
  application_id: string;
  type: string;
  due_date: string;
  status: string;
  message_template: string | null;
  notes: string | null;
  is_auto_generated: boolean;
  completed_at: string | null;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  preferences: Record<string, unknown> | null;
  telegram_chat_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
