#!/usr/bin/env bun
export interface ComplexityDecision {
  item: string;
  concrete_problem: string;
  needed_now: boolean;
  simple_solution: string;
  simple_monthly_cost?: number;
  complex_solution: string;
  complex_monthly_cost?: number;
  operational_burden: string;
  specialist_roles?: string[];
  new_failure_modes: string[];
  activation_trigger?: string;
  migration_path?: string;
}

export function validateDeferredComplexity(d: ComplexityDecision): string[] {
  const errors: string[] = [];
  if (!d.needed_now) {
    if (!d.simple_solution) errors.push('current simpler solution required');
    if (!d.activation_trigger) errors.push('measurable activation trigger required');
    if (!d.migration_path) errors.push('migration path required');
  }
  if (!d.concrete_problem) errors.push('concrete problem required');
  if (!d.operational_burden) errors.push('operational burden required');
  return errors;
}

export function defenderCostAmplification(attackerCost: number, defenderCost: number, threshold = 10): { amplified: boolean; ratio: number } {
  const ratio = attackerCost <= 0 ? Number.POSITIVE_INFINITY : defenderCost / attackerCost;
  return { amplified: ratio >= threshold, ratio };
}
