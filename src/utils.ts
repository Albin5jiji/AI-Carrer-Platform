import { readinessWeights } from "./data";
import type { ScoreKey } from "./types";

export const scoreLabels: Record<ScoreKey, string> = {
  academics: "Academic Performance",
  skills: "Skill Match",
  projects: "Project Relevance",
  certifications: "Certifications",
  resume: "Resume Quality",
  interview: "Interview Performance",
};

export function calculateReadinessScore(scores: Record<ScoreKey, number>) {
  const entries = Object.entries(scores) as [ScoreKey, number][];
  const total = entries.reduce((sum, [key, value]) => {
    return sum + value * (readinessWeights[key] / 100);
  }, 0);

  return Math.round(total);
}

export function getReadinessLevel(score: number) {
  if (score >= 85) return "Placement Ready";
  if (score >= 70) return "Nearly Ready";
  return "Needs Guided Improvement";
}

export function getRecommendation(score: number) {
  if (score >= 85) {
    return "Focus on company-specific interview practice and keep resume evidence current.";
  }

  if (score >= 70) {
    return "Improve weak skill areas, complete mentor feedback, and repeat mock interviews.";
  }

  return "Build project evidence, complete missing certifications, and schedule mentor review.";
}
