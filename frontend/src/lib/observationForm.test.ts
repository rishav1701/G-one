import {expect,test} from 'vitest';
import {observationFormError,observationPayload} from './observationForm';

test('requires at least one measured parameter',()=>{
 expect(observationFormError({})).toBe('Enter at least one observation value.');
});
test('requires oxygen status when oxygen saturation is entered',()=>{
 expect(observationFormError({spo2:'97'})).toMatch(/supplemental oxygen/);
 expect(observationFormError({spo2:'97',supplemental_o2:'no'})).toBeUndefined();
});
test('keeps entered values and provenance in the submission payload',()=>{
 const value=observationPayload({respiration_rate:'18',spo2:'97',supplemental_o2:'no',temperature:'37.1'},'admission-1','2026-11-06T00:00:00Z','manual-1');
 expect(value).toMatchObject({admission_id:'admission-1',respiration_rate:18,spo2:97,supplemental_o2:false,temperature:'37.1',source:'manual',source_record_id:'manual-1',is_simulated:true});
});

test('rejects values outside technical entry bounds',()=>{
 expect(observationFormError({pulse:'301'})).toMatch(/technical entry range/);
 expect(observationFormError({pulse:'70'})).toBeUndefined();
});