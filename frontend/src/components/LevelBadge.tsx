import {AlertCircle,CheckCircle2,MinusCircle,AlertTriangle,Clock3} from 'lucide-react';
import type {Level} from '../lib/clinical';
const style:Record<Level,string>={LOW:'low',LOW_MEDIUM:'low-medium',MEDIUM:'medium',HIGH:'high',INCOMPLETE:'incomplete',STALE:'stale',NO_DATA:'stale'};
const icons={LOW:CheckCircle2,LOW_MEDIUM:AlertTriangle,MEDIUM:AlertTriangle,HIGH:AlertCircle,INCOMPLETE:MinusCircle,STALE:Clock3,NO_DATA:MinusCircle} as const;
export function LevelBadge({level}:{level:Level}){const Icon=icons[level];const label=level==='INCOMPLETE'?'Assessment limited':level==='NO_DATA'?'No data':level.replace('_',' ');return <span className={`badge badge-${style[level]}`}><Icon aria-hidden="true" size={14}/><span>{label}</span></span>}
