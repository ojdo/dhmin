import dhmin
import dhmintools
import numpy as np
import pandas as pd
import pandashp as pdshp
import pyomo.environ
from pyomo.opt.base import SolverFactory

# config
vertex_file = 'shp/mnl/vertex'
edge_file = 'shp/mnl/edge'
params = {'r_heat':0.07} # only specify changed values
timesteps = [(1600,.8),(1040,.5)] # list of (duration [hours], scaling_factor) tuples
                              # annual fulload hours = sum(t, duration[t]*sf[t]) = 1800
     
# read vertices and edges from shapefiles...
vertex = pdshp.read_shp(vertex_file)
edge = pdshp.read_shp(edge_file)
# ... and set indices to agree with Excel format
vertex.set_index(['Vertex'], inplace=True)
edge.set_index(['Edge', 'Vertex1', 'Vertex2'], inplace=True)

# at this point, rundh.py and rundhshp.py work identically!
# dhmin.create_model must not rely on vertex/edge DataFrames to contain any
# geometry information

# get model
# create instance
# solver interface (GLPK)
model = dhmin.create_model(vertex, edge, params, timesteps)
solver = SolverFactory('glpk')
instance.write('rundhshp.lp', io_options={'symbolic_solver_labels':True})
result = solver.solve(instance, timelimit=30, tee=True)
instance.solutions.load_from(result)

# use special-purpose function to plot power flows (works unchanged!)
# dhmintools.plot_flows_min(instance)

# read time-independent variable values to DataFrame
# (list all variables using dhmin.list_entities(instance, 'variables')
caps = dhmin.get_entities(instance, ['Pmax', 'x'])
costs = dhmin.get_entity(instance, 'costs')

# remove Edge from index, so that edge and caps are both indexed on
# (vertex, vertex) tuples, i.e. their indices match for identical edges
edge.reset_index('Edge', inplace=True)

# change index names to 'Vertex1', 'Vertex2' from auto-inferred labels 
# 'vertex','vertex_'
caps.index.names = edge.index.names.copy()

# join
edge_with_caps = edge.join(caps)
# pdshp.write_shp(edge_with_caps, 'shp/mnl/edge_w_caps') # already prepared


# DEBUGGING
flows = dhmin.get_entities(instance, ['Pin', 'Pot'])
Pin = flows.fillna(0).Pin.round()
Pin = Pin[Pin>0].unstack().fillna(0) 
Pin.index.names = edge.index.names.copy()
print("Pin:\n")
print(Pin)

Pmax = caps.fillna(0).Pmax.round()
Pmax = Pmax[Pmax>0].fillna(0)
print("Pmax:\n")
print(Pmax)

# write findings to Excel file
xls = pd.ExcelWriter('debugging.xlsx')
pd.DataFrame(Pin).to_excel(xls, sheet_name='Pin')
pd.DataFrame(Pmax).to_excel(xls, sheet_name='Pmax')
flows.fillna(0).apply(np.round).to_excel(xls, sheet_name='Flows')
xls.save()

