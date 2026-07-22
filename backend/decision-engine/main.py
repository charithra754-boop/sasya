import os
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from ortools.linear_solver import pywraplp
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("decision-engine")

app = FastAPI(title="SasyaAI Decision Engine & Constraints Solver", version="0.1.0")

# ==============================================================================
# Pydantic Schemas
# ==============================================================================

class CropOption(BaseModel):
    crop_name: str
    expected_yield_kg_per_hectare: float
    expected_price_per_kg: float
    cost_per_hectare: float
    water_required_liters_per_hectare: float

class OptimizationRequest(BaseModel):
    total_land_hectares: float
    water_budget_liters: float
    capital_budget_rupees: float
    crop_options: List[CropOption]

class AllocationResult(BaseModel):
    crop_name: str
    allocated_hectares: float
    expected_yield_kg: float
    expected_profit_rupees: float
    water_used_liters: float
    cost_rupees: float

class OptimizationResponse(BaseModel):
    status: str
    optimal_profit_rupees: float
    allocations: List[AllocationResult]
    total_water_used_liters: float
    total_capital_used_rupees: float
    total_land_used_hectares: float

class VerificationRequest(BaseModel):
    proposed_allocations: Dict[str, float]  # Crop Name -> Hectares
    crop_options: List[CropOption]
    total_land_hectares: float
    water_budget_liters: float
    capital_budget_rupees: float

class VerificationResponse(BaseModel):
    is_safe: bool
    violations: List[str]
    total_water_used_liters: float
    total_capital_used_rupees: float
    total_land_used_hectares: float

# ==============================================================================
# Endpoints
# ==============================================================================

@app.get("/health")
@app.get("/api/v1/decision-engine/health")
def health():
    return {"status": "healthy", "service": "decision-engine-service"}

@app.post("/api/v1/decision-engine/optimize", response_model=OptimizationResponse)
def optimize_crop_allocation(payload: OptimizationRequest):
    logger.info(f"Decision Engine optimizing crop allocation across {payload.total_land_hectares} ha")
    
    # 1. Initialize Google OR-Tools GLOP (Linear Programming) solver
    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        raise HTTPException(status_code=500, detail="Google OR-Tools solver could not be initialized")

    # 2. Define decision variables
    # x[i] = hectares of land allocated to crop i
    x = {}
    for idx, crop in enumerate(payload.crop_options):
        # Hectares allocated must be non-negative: 0 <= x[i] <= total_land
        x[idx] = solver.NumVar(0.0, payload.total_land_hectares, f"x_{crop.crop_name}")

    # 3. Add Constraints
    # Constraint 1: Total land constraint -> sum(x[i]) <= total_land
    land_constraint = solver.Constraint(0.0, payload.total_land_hectares, "total_land_limit")
    for idx in range(len(payload.crop_options)):
        land_constraint.SetCoefficient(x[idx], 1.0)

    # Constraint 2: Water budget constraint -> sum(water_required_i * x[i]) <= water_budget
    water_constraint = solver.Constraint(0.0, payload.water_budget_liters, "water_budget_limit")
    for idx, crop in enumerate(payload.crop_options):
        water_constraint.SetCoefficient(x[idx], crop.water_required_liters_per_hectare)

    # Constraint 3: Capital/budget constraint -> sum(cost_i * x[i]) <= capital_budget
    capital_constraint = solver.Constraint(0.0, payload.capital_budget_rupees, "capital_budget_limit")
    for idx, crop in enumerate(payload.crop_options):
        capital_constraint.SetCoefficient(x[idx], crop.cost_per_hectare)

    # 4. Define Objective Function
    # Maximize Profit: sum((yield_i * price_i - cost_i) * x[i])
    objective = solver.Objective()
    for idx, crop in enumerate(payload.crop_options):
        profit_per_hectare = (crop.expected_yield_kg_per_hectare * crop.expected_price_per_kg) - crop.cost_per_hectare
        objective.SetCoefficient(x[idx], profit_per_hectare)
    objective.SetMaximization()

    # 5. Solve the optimization problem
    solver_status = solver.Solve()

    if solver_status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
        logger.warning("Optimization failed to find an optimal or feasible solution")
        return OptimizationResponse(
            status="INFEASIBLE",
            optimal_profit_rupees=0.0,
            allocations=[],
            total_water_used_liters=0.0,
            total_capital_used_rupees=0.0,
            total_land_used_hectares=0.0
        )

    # 6. Extract results
    allocations = []
    total_water = 0.0
    total_capital = 0.0
    total_land = 0.0

    for idx, crop in enumerate(payload.crop_options):
        allocated_val = x[idx].solution_value()
        if allocated_val > 1e-4:  # Filter out crops with tiny decimal allocations
            exp_yield = allocated_val * crop.expected_yield_kg_per_hectare
            exp_profit = (exp_yield * crop.expected_price_per_kg) - (allocated_val * crop.cost_per_hectare)
            w_used = allocated_val * crop.water_required_liters_per_hectare
            c_used = allocated_val * crop.cost_per_hectare

            allocations.append(AllocationResult(
                crop_name=crop.crop_name,
                allocated_hectares=round(allocated_val, 2),
                expected_yield_kg=round(exp_yield, 2),
                expected_profit_rupees=round(exp_profit, 2),
                water_used_liters=round(w_used, 2),
                cost_rupees=round(c_used, 2)
            ))
            
            total_water += w_used
            total_capital += c_used
            total_land += allocated_val

    logger.info(f"Optimal crop allocation calculated successfully. Net profit: ₹{solver.Objective().Value():.2f}")

    return OptimizationResponse(
        status="OPTIMAL" if solver_status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
        optimal_profit_rupees=round(solver.Objective().Value(), 2),
        allocations=allocations,
        total_water_used_liters=round(total_water, 2),
        total_capital_used_rupees=round(total_capital, 2),
        total_land_used_hectares=round(total_land, 2)
    )

@app.post("/api/v1/decision-engine/verify", response_model=VerificationResponse)
def verify_proposed_plan(payload: VerificationRequest):
    violations = []
    total_water = 0.0
    total_capital = 0.0
    total_land = 0.0

    # Build crop option lookup map
    options_map = {c.crop_name: c for c in payload.crop_options}

    for crop_name, hectares in payload.proposed_allocations.items():
        if hectares < 0:
            violations.append(f"Allocation for {crop_name} cannot be negative: {hectares} ha")
            continue
            
        total_land += hectares
        if crop_name not in options_map:
            violations.append(f"Crop '{crop_name}' is not in the allowed crop options list")
            continue
            
        crop_opt = options_map[crop_name]
        total_water += hectares * crop_opt.water_required_liters_per_hectare
        total_capital += hectares * crop_opt.cost_per_hectare

    # Check bounds violations
    if total_land > payload.total_land_hectares:
        violations.append(f"Total land allocated ({total_land:.2f} ha) exceeds farm limit of {payload.total_land_hectares:.2f} ha")
        
    if total_water > payload.water_budget_liters:
        violations.append(f"Total water consumption ({total_water:.2f} L) exceeds safe budget of {payload.water_budget_liters:.2f} L")
        
    if total_capital > payload.capital_budget_rupees:
        violations.append(f"Total input costs (₹{total_capital:.2f}) exceed capital budget of ₹{payload.capital_budget_rupees:.2f}")

    is_safe = len(violations) == 0
    return VerificationResponse(
        is_safe=is_safe,
        violations=violations,
        total_water_used_liters=round(total_water, 2),
        total_capital_used_rupees=round(total_capital, 2),
        total_land_used_hectares=round(total_land, 2)
    )
