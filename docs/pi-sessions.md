 What Hindsight docs say

 Relevant retain guidance:

- retain full conversation as one item
- use stable document_id
- re-retain full updated content with same document_id
- default replace deletes old memories and reprocesses
- append exists for growing docs, but docs describe sending new content only
- best-practices says retain after each turn or session ends
- do not retain and then require recall from that write in the same turn

 So for your desired mode, session-end retain is explicitly doc-aligned.

 What Pi gives us for “session end”

 Pi has practical lifecycle events:

- session_shutdown
  - reasons: "quit" | "reload" | "new" | "resume" | "fork"
- session_before_fork
- session_before_switch
- session_start
  - reasons: "startup" | "reload" | "new" | "resume" | "fork"
- session_before_compact
- session_compact
- session_tree
- agent_end
- turn_end

 So the minimal retain trigger should be:

 ```text
   session_shutdown                                                                                                                                                                                
 ```

 for:

 ```text
   quit, new, resume, fork                                                                                                                                                                         
 ```

 Probably not reload unless we intentionally want it.

 Compaction needs its own rule:

 ```text
   session_compact                                                                                                                                                                                 
 ```

 because after compaction, active context changes even though full JSONL history remains.

 Forking:

 ```text
   session_shutdown(reason="fork")                                                                                                                                                                 
 ```

 should retain the old branch/session before switching into the forked session.

 Proposed production behavior

### Default

 Retain once per Pi session lifecycle boundary:

 ```text
   session_shutdown: quit/new/resume/fork                                                                                                                                                          
 ```

 Use:

 ```text
   update_mode: replace                                                                                                                                                                            
   document_id: pi-session:<session_id>:<active_branch_or_leaf>                                                                                                                                    
 ```

### Compaction

 On session_compact, retain a compaction artifact separately, not as if it were a full session end:

 ```text
   document_id: pi-compaction:<session_id>:<compaction_entry_id>                                                                                                                                   
 ```

 This lets memory know what got summarized without pretending the whole session ended.

### Resume

 On resume, don’t retain immediately. Pi already has the session file. Retain when that resumed session shuts down again.

### Fork

 Fork becomes separate memory lineage:

 ```text
   pi-session:<new_session_id>:...                                                                                                                                                                 
   metadata.parent_session_file                                                                                                                                                                    
   metadata.fork_source_entry_id                                                                                                                                                                   
 ```

 Do not merge fork back into parent memory automatically.
