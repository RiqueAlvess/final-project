import { apiClient } from "./api";

export interface Campaign {
  id: number;
  name: string;
  description: string;
  status: "DRAFT" | "ACTIVE" | "CLOSED";
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
  total_invites: number;
  total_answered: number;
}

export interface SurveyInvite {
  id: number;
  campaign: number;
  campaign_name: string;
  email_hash: string;
  token: string;
  send_status: "PENDING" | "SENT" | "FAILED";
  response_status: "PENDING" | "ANSWERED";
  sent_at: string | null;
  created_at: string;
  unidade_id: number | null;
  setor_id: number | null;
}

export interface HSEQuestion {
  id: number;
  text: string;
  dimension: number;
  dimension_name: string;
  order: number;
}

export interface HSEDimension {
  id: number;
  name: string;
  dimension_type: "POSITIVE" | "NEGATIVE";
  order: number;
  questions: HSEQuestion[];
}

export interface SurveyData {
  campaign: { id: number; name: string; description: string };
  dimensions: HSEDimension[];
}

export interface DimensionScoreSummary {
  dimension__id: number;
  dimension__name: string;
  dimension__dimension_type: string;
  dimension__order: number;
  avg_score: number;
  avg_risk: number;
}

export interface DashboardData {
  campaign: Campaign;
  summary: {
    total_invites: number;
    total_answered: number;
    adhesion_rate: number;
    igrp: number;
    high_risk_pct: number;
    dimension_scores: DimensionScoreSummary[];
    risk_distribution: Record<string, number>;
  };
  gender_scores: Array<{ gender: string; dimension__name: string; dimension__order: number; avg_score: number }>;
  age_range_scores: Array<{ age_range: string; dimension__name: string; dimension__order: number; avg_score: number }>;
  sector_heatmap: Array<{ setor_id: number; dimension__name: string; avg_risk: number }>;
  critical_sectors: Array<{ setor_id: number; high_risk_count: number; avg_risk: number }>;
  demographic_groups: {
    by_gender: Array<{ gender: string; avg_risk: number }>;
    by_age_range: Array<{ age_range: string; avg_risk: number }>;
  };
}

export interface DashboardFilters {
  unidades: Array<{ id: number; name: string }>;
  setores: Array<{ id: number; name: string; unidade_id: number; unidade__name: string }>;
}

export interface DashboardFilterParams {
  unidade_ids?: number[];
  setor_ids?: number[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

const campaignsApi = {
  list: () => apiClient.get<PaginatedResponse<Campaign>>("/api/campaigns/"),

  create: (data: { name: string; description: string }) =>
    apiClient.post<Campaign>("/api/campaigns/", data),

  update: (id: number, data: Partial<{ name: string; description: string; status: string }>) =>
    apiClient.patch<Campaign>(`/api/campaigns/${id}/`, data),

  delete: (id: number) => apiClient.delete(`/api/campaigns/${id}/`),

  activate: (id: number) =>
    apiClient.post<Campaign>(`/api/campaigns/${id}/activate/`),

  close: (id: number) =>
    apiClient.post<Campaign>(`/api/campaigns/${id}/close/`),

  // Invites
  listInvites: (campaignId: number, page = 1) =>
    apiClient.get<PaginatedResponse<SurveyInvite>>(
      `/api/campaigns/${campaignId}/invites/?page=${page}`
    ),

  importInvites: (campaignId: number) =>
    apiClient.post<{ created: number; total: number }>(
      `/api/campaigns/${campaignId}/invites/import/`
    ),

  sendInvites: (campaignId: number, inviteIds: number[]) =>
    apiClient.post<{ enqueued: number }>(
      `/api/campaigns/${campaignId}/invites/send/`,
      { invite_ids: inviteIds }
    ),

  // Dashboard
  getDashboard: (campaignId: number, filters?: DashboardFilterParams) => {
    const params = new URLSearchParams();
    if (filters?.unidade_ids?.length) {
      params.set('unidade_ids', filters.unidade_ids.join(','));
    }
    if (filters?.setor_ids?.length) {
      params.set('setor_ids', filters.setor_ids.join(','));
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<DashboardData>(`/api/campaigns/${campaignId}/dashboard/${query}`);
  },

  getDashboardFilters: (campaignId: number) =>
    apiClient.get<DashboardFilters>(`/api/campaigns/${campaignId}/dashboard/filters/`),
};

export const surveyApi = {
  validate: (token: string) =>
    apiClient.get<SurveyData>(`/api/campaigns/survey/${token}/`),

  submit: (
    token: string,
    data: {
      consent: boolean;
      gender?: string;
      age_range?: string;
      answers: Array<{ question_id: number; value: number }>;
    }
  ) => apiClient.post(`/api/campaigns/survey/${token}/submit/`, data),
};

export default campaignsApi;
