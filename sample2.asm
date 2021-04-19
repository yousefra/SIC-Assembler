COPY       START     0000                COMMENT
FIRST      STL       RETADR              COMMENT
CLOOP      JSUB      RDREC              
           LDA       LENGTH              COMMENTCOMMENTCOMMENTCOMMENTCOeeeeeeeeeeeeeeeeeeeMMENT
           COMP      ZERO                COMMENTCOMMENT
           JEQ       ENDFIL             
           JSUB      WRREC               COMMENTCOMMENT
           J         CLOOP              
ENDFIL     LDA       EOF                
           STA       BUFFER              COMMENT
           LDA       THREE              
           STA       LENGTH             
           JSUB      WRREC               COMMENT
           LDL       RETADR             
           RSUB                      
EOF        BYTE      C'EOF'             
THREE      WORD      3                  
ZERO       WORD      0                  
RETADR     RESW      1                   COMMENTCOMMENTCOMMENT
LENGTH     RESW      1                  
BUFFER     RESB      4096               
.               
.        SUBROUTINE TO READ RECORD INTO BUFFER
.                
RDREC      LDX       ZERO               
           LDA       ZERO                COMMENT
RLOOP      TD        INPUT              
           JEQ       RLOOP              
           RD        INPUT               COMMENTCOMMENTCOMMENT
           COMP      ZERO                
           JEQ       EXIT               
           STCH      BUFFER,X           
           TIX       MAXLEN             
           JLT       RLOOP              
EXIT       STX       LENGTH             
           RSUB                      
INPUT      BYTE      X'F1'              
MAXLEN     WORD      4096                                    
.                
.        SUBROUTINE TO WRITE RECORD FROM BUFFER
.               
WRREC      LDX       ZERO               
WLOOP      TD        OUTPUT             
           JEQ       WLOOP              
           LDCH      BUFFER,X           
           WD        OUTPUT             
           TIX       LENGTH             
           JLT       WLOOP              
           RSUB                      
OutPUT     BYTE      X'50'              
.
.       TESTING LITERALS
.
           LDA       =C'EOF'            
           RSUB                      
           LDA       =X'05'             
           LDA       =X'07'             
           RSUB                      
           LTORG                     
           LDA       =C'OFE'            
           LDA       =X'05'             
           END       FIRST              