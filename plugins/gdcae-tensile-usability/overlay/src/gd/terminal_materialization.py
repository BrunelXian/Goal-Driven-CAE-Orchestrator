"""Resume only the same completed native B evidence, never an execution request.

One immutable extraction is persisted in the existing campaign database before
the private seal/scientific settlement. No independent budget is maintained.
"""
import json
import continuation as c
TABLE='tensile_native_materializations'

def extract_once(camp,row):
    import native_feedback as nf
    from abqjobpilot.local_credentials import private_value,read_private
    from abqjobpilot.service_lifecycle import write_new
    c.require(row['phase']=='B','B_MATERIALIZATION_ONLY')
    req,reader,binding,manager=nf.source(camp,row)
    identity=dict(schema='completed-native-b-materialization-v1',phase='B',project=req['project'],candidate=req['candidate_id'],
        contract=camp.pin,original_request=c.case.hashbytes(row['request']),binding=binding,reader_sha256=c.sha(reader))
    camp.db.execute('BEGIN IMMEDIATE')
    try:
        fresh=camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone()
        c.require(fresh['state']=='INTENT' and fresh['request']==row['request'],'SAME_SCIENTIFIC_INTENT_REQUIRED')
        camp.verified_rows(terminal_structure_only=True)
        camp.db.execute('CREATE TABLE IF NOT EXISTS '+TABLE+'(phase TEXT PRIMARY KEY,run_id TEXT UNIQUE,identity BLOB,identity_pin TEXT,extraction BLOB,extraction_pin TEXT,result BLOB,result_pin TEXT)')
        stored=camp.db.execute('SELECT * FROM '+TABLE+" WHERE phase='B'").fetchone()
        reused=stored is not None
        if stored is None:
            # Holding this same-DB write lease serializes materialization. Reads
            # of completed ODB/native evidence remain read-only. A crash before
            # commit has no durable result and never grants Solver retry rights.
            extraction=nf.read_extraction(camp,req,reader,binding)
            c.require(nf.source(camp,row)[2]==binding,'TERMINAL_SOURCE_CHANGED')
            result=nf.evaluate(camp,req,binding,extraction)
            camp.db.execute('INSERT INTO '+TABLE+' VALUES(?,?,?,?,?,?,?,?)',('B',binding['run_id'],c.pack(identity),c.pin(identity),c.pack(extraction),c.pin(extraction),c.pack(result),c.pin(result)))
        else:
            c.require(stored['run_id']==binding['run_id'] and stored['identity']==c.pack(identity) and stored['identity_pin']==c.pin(identity)
                and c.case.hashbytes(stored['extraction'])==stored['extraction_pin'] and c.case.hashbytes(stored['result'])==stored['result_pin'],'MATERIALIZATION_IDENTITY_CHANGED')
            extraction=json.loads(stored['extraction']);result=nf.evaluate(camp,req,binding,extraction)
            c.require(c.pack(result)==stored['result'],'MATERIALIZED_RESULT_CHANGED')
        camp.db.commit()
    except BaseException:camp.db.rollback();raise
    c.require(nf.source(camp,row)[2]==binding,'TERMINAL_SOURCE_CHANGED')
    seal={'result_digest':c.pin(result),'binding_digest':c.pin(binding)};path=manager._path('tensile-feedback.json')
    if path.exists():c.require(read_private(manager.context,path)==seal,'EXISTING_FEEDBACK_SEAL_CHANGED')
    else:
        if reused:
            # An unsealed cache is not authoritative evidence. Re-read the same
            # immutable ODB through the reviewed reader before first sealing.
            actual=nf.read_extraction(camp,req,reader,binding)
            c.require(c.pack(actual)==c.pack(extraction) and nf.evaluate(camp,req,binding,actual)==result
                and nf.source(camp,row)[2]==binding,'UNSEALED_CACHE_NOT_REPRODUCED')
        write_new(path,private_value(manager.context,seal))
    return result

def complete_intent(camp,row):
    """CAS the existing scientific INTENT to NATIVE using verified cached facts."""
    import native_feedback as nf
    result=extract_once(camp,row);raw=c.pack(result)
    nf.verify(camp,dict(row,result=raw))
    camp.db.execute('BEGIN IMMEDIATE')
    try:
        rows=camp.verified_rows(terminal_structure_only=True);current=rows[-1]
        c.require(current['phase']=='B' and current['request']==row['request'],'SCIENTIFIC_CAS_CHANGED')
        if current['state']!='INTENT':
            c.require(current['result']==raw and current['state']==camp.assessment_state('B',result['assessment']),'SCIENTIFIC_CAS_CHANGED')
        else:
            changed=camp.db.execute("UPDATE stages SET state=?,result=? WHERE phase='B' AND state='INTENT' AND request=?",
                (camp.assessment_state('B',result['assessment']),raw,row['request']))
            c.require(changed.rowcount==1,'SCIENTIFIC_CAS_CHANGED');camp.record('B','NATIVE',row['request'],raw)
        camp.db.commit()
        return dict(status='SAME_NATIVE_INTENT_COMMITTED',phase='B',feedback=result,budget=camp.counts(camp.verified_rows()),execution_authorized=False)
    except BaseException:camp.db.rollback();raise
