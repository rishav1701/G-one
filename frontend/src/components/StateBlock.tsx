import type {ReactNode} from 'react';
export function StateBlock({state,children}:{state:'loading'|'empty'|'error';children?:ReactNode}){const text={loading:'Loading…',empty:'No records to display',error:'Unable to load this information'}[state];return <div role={state==='error'?'alert':'status'} className="state-block">{children||text}</div>}
