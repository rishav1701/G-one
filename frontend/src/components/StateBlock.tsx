import type {ReactNode} from 'react';
type State='loading'|'empty'|'error'|'stale'|'forbidden'|'no-data';
const copy:Record<State,string>={loading:'Loading…',empty:'No records to display',error:'Unable to load this information',stale:'This information is stale. Check the last-updated time.',forbidden:'You do not have access to this information.', 'no-data':'No current data is available.'};
export function StateBlock({state,children}:{state:State;children?:ReactNode}){const alert=state==='error'||state==='forbidden';return <div role={alert?'alert':'status'} className="state-block" data-state={state}>{children||copy[state]}</div>}
