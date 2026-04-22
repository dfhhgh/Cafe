from .ast import *
from Scanner.TokenType import TokenType as TT


class Symbol:
    def __init__(self, name, data_type):
        self.name = name
        self.data_type = data_type


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def declare(self, name, symbol):
        if name in self.scopes[-1]:
            raise Exception(f"❌ Variable '{name}' already declared in this scope")
        self.scopes[-1][name] = symbol

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"❌ Undeclared variable '{name}'")


class BottomUpParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.stack = []
        self.current = 0

        self.symbol_table = SymbolTable()

        # ✅ FIX 4: track current function return type for return-stmt validation
        self.current_function_type = None

        # ✅ FIX 1 & 2 & 5: each entry mirrors a shifted '{' and stores whether
        # a new scope was opened for it ('func' | 'block' | None).
        # Every reduction that consumes a '{' must pop exactly one entry from here.
        self.scope_stack = []

        self.REL_OPS = {TT.GT, TT.LT, TT.EQ, TT.NE, TT.GTE, TT.LTE}
        #ده Set (مجموعة) فيها كل operators الخاصة بالمقارنة (Relational Operators)

    # ─────────────────────────────────────────────────────────────────────────
    # PARSE ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────

    def parse(self):
        while self.current < len(self.tokens):
            token = self.tokens[self.current]
            self.stack.append(token)
            self.current += 1

            # ✅ FIX 1 & 2 & 5 (core mechanism):
            # Scope is pushed HERE – BEFORE the block's inner statements are
            # ever shifted and reduced.  This is the only correct point in a
            # bottom-up parser to open a scope, because by the time _block()
            # fires, all inner declarations have already been processed.
            if token.type == TT.LBRACE: #TT هو اختصار (alias) لـ:TokenType
                self._on_lbrace_shifted()

            self._reduce()

        return self._build_program()

    # ─────────────────────────────────────────────────────────────────────────
    # SCOPE MANAGEMENT ON '{'
    # ─────────────────────────────────────────────────────────────────────────

    def _on_lbrace_shifted(self):
        """
        Called the moment '{' lands on the stack.

        Decision tree
        ─────────────
        1. Stack before '{' matches a function header
           → push scope AND register all parameters right now,
             so they are visible when the body's statements are parsed.

        2. Token before '{' is ')' (if / while / for / func-no-params)
           → push a plain block scope.

        3. Otherwise (array literal, etc.)
           → push None so scope_stack stays in sync without opening a scope.
        """
        func_params = self._detect_function_header()
        if func_params is not None:
            self.symbol_table.push_scope()
            for p in func_params:
                self.symbol_table.declare(p.name, Symbol(p.name, p.type))
            self.scope_stack.append('func')
            return

        # Block that follows a closing ')' → if / while / for
        prev = self.stack[-2] if len(self.stack) >= 2 else None
        if prev is not None and self._is_token(prev, TT.RPAREN):
            self.symbol_table.push_scope()
            self.scope_stack.append('block')
        else:
            self.scope_stack.append(None)   # array literal or switch body

    def _detect_function_header(self):
        """
        Inspect the stack just before the shifted '{' for the pattern:

            dtype  RECIPE  IdentifierNode  [LPAREN]  [params/ParamListNode]  [RPAREN]
        
        OR (when params have already been reduced):
        
            dtype  RECIPE  IdentifierNode  ParamListNode  
            dtype  RECIPE  IdentifierNode  ParamNode
            dtype  RECIPE  IdentifierNode  (no params, no LPAREN/RPAREN either)

        Returns a (possibly empty) list of ParamNode on success, else None.
        """
        s = self.stack[:-1]   # exclude the just-shifted '{'
        n = len(s)

        if n < 3:
            return None

        # Pattern 1: dtype RECIPE IdentifierNode ParamListNode (params already reduced)
        if n >= 4:
            dtype, recipe, name, params_or_last = s[-4], s[-3], s[-2], s[-1]
            if (self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) and
                self._is_token(recipe, TT.RECIPE) and
                isinstance(name, IdentifierNode) and
                isinstance(params_or_last, ParamListNode)):
                return params_or_last.params

        # Pattern 2: dtype RECIPE IdentifierNode ParamNode (single param, already reduced)
        if n >= 4:
            dtype, recipe, name, param = s[-4], s[-3], s[-2], s[-1]
            if (self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) and
                self._is_token(recipe, TT.RECIPE) and
                isinstance(name, IdentifierNode) and
                isinstance(param, ParamNode)):
                return [param]

        # Pattern 3: dtype RECIPE IdentifierNode LPAREN ... RPAREN (old pattern, tokens not yet consumed)
        if not self._is_token(s[-1], TT.RPAREN):
            return None if n < 4 else None

        # Slot before RPAREN: either LPAREN (no params) or a param node
        params = []
        i = n - 2

        if self._is_token(s[i], TT.LPAREN):
            lp_idx = i                              # no-param function
        elif isinstance(s[i], (ParamNode, ParamListNode)):
            p_item = s[i]
            i -= 1
            if i < 0 or not self._is_token(s[i], TT.LPAREN):
                return None
            lp_idx = i
            params = p_item.params if isinstance(p_item, ParamListNode) else [p_item]
        else:
            return None

        # Before '(': function name as IdentifierNode
        if lp_idx < 1 or not isinstance(s[lp_idx - 1], IdentifierNode):
            return None

        # Before name: RECIPE keyword
        if lp_idx < 2 or not self._is_token(s[lp_idx - 2], TT.RECIPE):
            return None

        # Before RECIPE: return-type keyword
        type_tokens = [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]
        if lp_idx < 3 or not self._is_token(s[lp_idx - 3], type_tokens):
            return None

        return params   # success – list may be empty for no-param functions

    # ─────────────────────────────────────────────────────────────────────────
    # PROGRAM
    # ─────────────────────────────────────────────────────────────────────────

    def _build_program(self):
        leftover = [x for x in self.stack if not isinstance(x, Node)]
        if leftover:
            raise SyntaxError(f"Unparsed tokens: {leftover}")
        return ProgramNode([x for x in self.stack if isinstance(x, Node)])

    # ─────────────────────────────────────────────────────────────────────────
    # REDUCE DISPATCHER
    # ─────────────────────────────────────────────────────────────────────────

    def _reduce(self):
        while True:
        # =========================
        # BASIC
        # =========================
            if self._remove_eof():       continue
            if self._literal():          continue

        # =========================
        # 🔥 STATEMENTS FIRST
        # =========================
            if self._var_decl():         continue
            if self._var_decl_no_init(): continue
            if self._assignment():       continue
            if self._print():            continue

        # =========================
        # CONTROL FLOW
        # =========================
            if self._block():            continue
            if self._if_else_stmt():     continue
            if self._if_elif_stmt():     continue
            if self._if_stmt():          continue
            if self._while_stmt():       continue
            if self._for_stmt():         continue

        # =========================
        # SWITCH
        # =========================
            if self._switch_case():      continue
            if self._switch_default():   continue
            if self._switch_stmt():      continue

        # =========================
        # FUNCTIONS
        # =========================
            if self._param():            continue
            if self._param_list():       continue
            if self._func_call():        continue
            if self._func_def():         continue
            if self._return_stmt():      continue

        # =========================
        # ARRAYS
        # =========================
            if self._array_values():     continue
            if self._array_decl():       continue

        # =========================
        # EXPRESSIONS
        # =========================
            if self._parenthesis():      continue
            if self._mul_div():          continue
            if self._add_sub():          continue
            if self._condition():        continue

        # =========================
        # 🔥 IDENTIFIER LAST
        # =========================
            if self._identifier():       continue

            break

    # ─────────────────────────────────────────────────────────────────────────
    # TYPE HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _map_type(self, token_type):
        return {
            TT.COUNT:   "number",
            TT.MEASURE: "number",
            TT.COIN:    "number",
            TT.NOTE:    "string",
            TT.EMO:     "string",
        }.get(token_type, "unknown")

    def _check_types(self, left, right):
        return left == right

    # ─────────────────────────────────────────────────────────────────────────
    # BASIC REDUCTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _remove_eof(self):
        if self._match_token(-1, TT.EOF):
            self.stack.pop()
            return True
        return False

    def _literal(self):#تحويل القيم البسيطة (Numbers / Strings) من Tokens إلى AST Nodes
        if self._match_token(-1, TT.NUMBER):
            token = self.stack.pop()
            node = LiteralNode(float(token.value))
            node.dtype = "number"
            self.stack.append(node)
            return True
        if self._match_token(-1, TT.STRING):
            token = self.stack.pop()
            node = LiteralNode(token.value)
            node.dtype = "string"
            self.stack.append(node)
            return True
        return False

    def _identifier(self):
        if not self._match_token(-1, TT.IDENTIFIER):
            return False

        token = self.stack.pop()

        # ✅ FIX 1 helper:
        # Parameter names and function names sit directly after a type keyword
        # or the RECIPE keyword on the stack.  They are not in the symbol table
        # yet, so we must NOT look them up – the enclosing reduction (_param /
        # _func_def) will assign the correct dtype afterwards.
        in_decl_context = (
            len(self.stack) >= 1 and
            self._is_token(
                self.stack[-1],
                [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO, TT.RECIPE]
            )
        )

        if in_decl_context:
            node = IdentifierNode(token.value)
            node.dtype = "unknown"          # resolved by _param or _func_def
        else:
            try:
                symbol = self.symbol_table.lookup(token.value)   # raises if undeclared
            except Exception:
                raise Exception(f"❌ Undefined identifier: {token.value}")
            node = IdentifierNode(token.value)
            node.dtype = symbol.data_type

        self.stack.append(node)
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # EXPRESSIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _parenthesis(self):
        if len(self.stack) >= 3:
            lp, inner, rp = self.stack[-3:]
            if self._is_token(lp, TT.LPAREN) and isinstance(inner, Node) \
               and self._is_token(rp, TT.RPAREN):
                self._pop(3)
                self.stack.append(inner)
                return True
        return False

    def _binary_expr(self, ops):
        if len(self.stack) < 3:
            return False
        left, op, right = self.stack[-3:]
        if isinstance(left, Node) and self._is_token(op, ops) and isinstance(right, Node):
            if not self._check_types(left.dtype, right.dtype):
                raise Exception("❌ Type mismatch in expression")
            node = BinaryExprNode(left, op.type, right)
            node.dtype = left.dtype
            self._pop(3)
            self.stack.append(node)
            return True
        return False

    def _mul_div(self):
        return self._binary_expr([TT.MULTIPLY, TT.DIVIDE])

    def _add_sub(self):
        if len(self.stack) < 3:
            return False
        left, op, right = self.stack[-3:]
        if isinstance(left, Node) and self._is_token(op, [TT.PLUS, TT.MINUS]) \
           and isinstance(right, Node):
            next_tok = self._peek()
            if next_tok and next_tok.type in [TT.MULTIPLY, TT.DIVIDE]:
                return False
            if not self._check_types(left.dtype, right.dtype):
                raise Exception("❌ Type mismatch in expression")
            node = BinaryExprNode(left, op.type, right)
            node.dtype = left.dtype
            self._pop(3)
            self.stack.append(node)
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # CONDITION
    # ─────────────────────────────────────────────────────────────────────────

    def _condition(self):
        if len(self.stack) < 3:
            return False
        left, op, right = self.stack[-3:]
        if isinstance(left, Node) and hasattr(op, "type") \
           and op.type in self.REL_OPS and isinstance(right, Node):
            if not self._check_types(left.dtype, right.dtype):
                raise Exception("❌ Type mismatch in condition")
            node = ConditionNode(left, op, right)
            node.dtype = "bool"
            self._pop(3)
            self.stack.append(node)
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # BLOCK
    # ─────────────────────────────────────────────────────────────────────────

    def _block(self):
        """
        Matches:  {  Stmt  }

        ✅ FIX 2: The matching scope was pushed the instant '{' was shifted
        (inside _on_lbrace_shifted), so every inner declaration already landed
        in that scope.  We only pop it here.
        """
        if len(self.stack) >= 3:
            l, stmt, r = self.stack[-3:]
            if self._is_token(l, TT.LBRACE) and isinstance(stmt, Node) \
               and self._is_token(r, TT.RBRACE):

                scope_type = self.scope_stack.pop() if self.scope_stack else None
                if scope_type is not None:
                    self.symbol_table.pop_scope()

                self._pop(3)
                self.stack.append(BlockNode([stmt]))
                return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # CONTROL FLOW
    # ─────────────────────────────────────────────────────────────────────────

    def _if_stmt(self):
        if len(self.stack) >= 5:
            check, lp, cond, rp, block = self.stack[-5:]
            if self._is_token(check, TT.CHECK) and self._is_token(lp, TT.LPAREN) \
               and isinstance(cond, Node) and self._is_token(rp, TT.RPAREN) \
               and isinstance(block, Node):
                self._pop(5)
                self.stack.append(IfNode(cond, block))
                return True
        return False

    def _if_else_stmt(self):
        if len(self.stack) >= 3:
            if_node, instead, else_block = self.stack[-3:]
            if isinstance(if_node, IfNode) and self._is_token(instead, TT.INSTEAD) \
               and isinstance(else_block, Node):
                self._pop(3)
                if_node.else_block = else_block
                self.stack.append(if_node)
                return True
        return False

    def _if_elif_stmt(self):
        if len(self.stack) >= 6:
            if_node, another_check, lp, cond, rp, block = self.stack[-6:]
            if isinstance(if_node, IfNode) \
               and self._is_token(another_check, TT.ANOTHER_CHECK) \
               and self._is_token(lp, TT.LPAREN) and isinstance(cond, Node) \
               and self._is_token(rp, TT.RPAREN) and isinstance(block, Node):
                self._pop(6)
                if_node.else_block = IfNode(cond, block)
                self.stack.append(if_node)
                return True
        return False

    def _while_stmt(self):
        if len(self.stack) >= 5:
            stir, lp, cond, rp, block = self.stack[-5:]
            if self._is_token(stir, TT.STIR) and self._is_token(lp, TT.LPAREN) \
               and isinstance(cond, Node) and self._is_token(rp, TT.RPAREN) \
               and isinstance(block, Node):
                self._pop(5)
                self.stack.append(WhileNode(cond, block))
                return True
        return False

    def _for_stmt(self):
        if len(self.stack) >= 8:
            refill, lp, assign, cond, semi, inc, rp, block = self.stack[-8:]
            if self._is_token(refill, TT.REFILL) and self._is_token(lp, TT.LPAREN) \
               and isinstance(assign, AssignNode) and isinstance(cond, Node) \
               and self._is_token(semi, TT.SEMICOLON) and isinstance(inc, Node) \
               and self._is_token(rp, TT.RPAREN) and isinstance(block, Node):
                self._pop(8)
                self.stack.append(ForNode(assign, cond, inc, block))
                return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # SWITCH
    # ─────────────────────────────────────────────────────────────────────────

    def _switch_case(self):
        if len(self.stack) >= 6:
            item, num, colon, stmts, done, semi = self.stack[-6:]
            if self._is_token(item, TT.ITEM) and self._is_token(num, TT.NUMBER) \
               and self._is_token(colon, TT.COLON) and isinstance(stmts, Node) \
               and self._is_token(done, TT.DONE) and self._is_token(semi, TT.SEMICOLON):
                self._pop(6)
                self.stack.append(CaseNode(num.value, stmts))
                return True
        return False

    def _switch_default(self):
        if len(self.stack) >= 3:
            any_drink, colon, stmts = self.stack[-3:]
            if self._is_token(any_drink, TT.ANY_DRINK) and \
               self._is_token(colon, TT.COLON) and isinstance(stmts, Node):
                self._pop(3)
                self.stack.append(DefaultCaseNode(stmts))
                return True
        return False

    def _switch_stmt(self):
        """
        Matches:  menu ( id ) { CaseNode* DefaultCaseNode? }

        Walks the stack backwards from '}' to collect all case / default nodes,
        then verifies the 'menu ( id ) {' header.
        """
        if len(self.stack) < 5:
            return False
        if not self._is_token(self.stack[-1], TT.RBRACE):
            return False

        case_list    = []
        default_case = None
        lb_idx       = -1
        i = len(self.stack) - 2

        while i >= 0:
            item = self.stack[i]
            if isinstance(item, CaseNode):
                case_list.insert(0, item)
                i -= 1
            elif isinstance(item, DefaultCaseNode):
                default_case = item
                i -= 1
            elif self._is_token(item, TT.LBRACE):
                lb_idx = i
                break
            else:
                return False

        if lb_idx < 4:
            return False

        menu = self.stack[lb_idx - 4]
        lp   = self.stack[lb_idx - 3]
        var  = self.stack[lb_idx - 2]
        rp   = self.stack[lb_idx - 1]

        if self._is_token(menu, TT.MENU) and self._is_token(lp, TT.LPAREN) \
           and isinstance(var, IdentifierNode) and self._is_token(rp, TT.RPAREN):

            # Keep scope_stack in sync with the '{' used for this switch body
            scope_type = self.scope_stack.pop() if self.scope_stack else None
            if scope_type is not None:
                self.symbol_table.pop_scope()

            total = len(self.stack) - (lb_idx - 4)
            self._pop(total)
            self.stack.append(SwitchNode(var.name, case_list, default_case))
            return True

        return False

    # ─────────────────────────────────────────────────────────────────────────
    # FUNCTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _param(self):
        if len(self.stack) >= 2:
            dtype, name = self.stack[-2:]
            if self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) \
               and isinstance(name, IdentifierNode):
                # Don't match if the next token is ASSIGN (indicates variable declaration, not parameter)
                next_token = self.tokens[self.current] if self.current < len(self.tokens) else None
                if next_token and next_token.type == TT.ASSIGN:
                    return False
                
                var_type = self._map_type(dtype.type)
                self._pop(2)
                self.stack.append(ParamNode(var_type, name.name if isinstance(name, IdentifierNode) else name.value))
                return True
        return False

    def _param_list(self):
        if len(self.stack) >= 3:
            p1, comma, p2 = self.stack[-3:]
            if isinstance(p1, ParamNode) and self._is_token(comma, TT.COMMA) \
               and isinstance(p2, (ParamNode, ParamListNode)):
                params = [p1] + (p2.params if isinstance(p2, ParamListNode) else [p2])
                self._pop(3)
                self.stack.append(ParamListNode(params))
                return True
        return False

    # ✅ FIX 4a: validate function calls at the call site
    def _func_call(self):
        """
        Matches:  IdentifierNode  (  )            – zero-argument call
                  IdentifierNode  (  Expr  )       – single-argument call

        Checks:
          • The identifier refers to a declared function (dtype = 'func<T>').
          • Produces a FuncCallNode with dtype = T.

        Note: multi-arg calls need a dedicated ArgListNode in ast.py; extend
        this method once the argument-list grammar is added.
        """
        # ── zero-arg call ────────────────────────────────────────────────────
        if len(self.stack) >= 3:
            fn, lp, rp = self.stack[-3:]
            if isinstance(fn, IdentifierNode) \
               and self._is_token(lp, TT.LPAREN) \
               and self._is_token(rp, TT.RPAREN):

                try:
                    symbol = self.symbol_table.lookup(fn.name)
                except Exception:
                    return False   # not resolvable yet; let other rules try

                if not symbol.data_type.startswith("func<"):
                    raise Exception(f"❌ '{fn.name}' is not a function")

                return_type = symbol.data_type[5:-1]
                self._pop(3)
                node = FuncCallNode(fn.name, [])
                node.dtype = return_type
                self.stack.append(node)
                return True

        # ── single-arg call ──────────────────────────────────────────────────
        if len(self.stack) >= 4:
            fn, lp, arg, rp = self.stack[-4:]
            if isinstance(fn, IdentifierNode) \
               and self._is_token(lp, TT.LPAREN) \
               and isinstance(arg, Node) \
               and self._is_token(rp, TT.RPAREN) \
               and not isinstance(arg, (ParamNode, ParamListNode)):   # guard: not func header

                try:
                    symbol = self.symbol_table.lookup(fn.name)
                except Exception:
                    return False

                if not symbol.data_type.startswith("func<"):
                    return False   # plain parenthesised expression; _parenthesis handles it

                return_type = symbol.data_type[5:-1]
                self._pop(4)
                node = FuncCallNode(fn.name, [arg])
                node.dtype = return_type
                self.stack.append(node)
                return True

        return False

    def _func_def(self):
        """
        Three variants:
          A) dtype RECIPE IdentNode LPAREN params RPAREN BlockNode   (with params, not reduced)
          B) dtype RECIPE IdentNode LPAREN        RPAREN BlockNode   (no params, not reduced)
          C) dtype RECIPE IdentNode ParamListNode BlockNode          (params already reduced to ParamListNode)
          D) dtype RECIPE IdentNode ParamNode     BlockNode          (single param already reduced)

        ✅ FIX 1: scope + param registration already happened in _on_lbrace_shifted
           before the body was parsed, so BlockNode was built in the correct scope.
           _func_def only needs to:
             • declare the function symbol in the OUTER scope  (✅ FIX 3)
             • set / restore current_function_type             (✅ FIX 4b)
        """
        type_tokens = [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]

        # ── variant C: params already reduced to ParamListNode ────────────────
        if len(self.stack) >= 5:
            dtype, recipe, name, params, block = self.stack[-5:]
            if self._is_token(dtype, type_tokens) \
               and self._is_token(recipe, TT.RECIPE) \
               and isinstance(name, IdentifierNode) \
               and isinstance(params, ParamListNode) \
               and isinstance(block, BlockNode):

                return_type = self._map_type(dtype.type)
                param_list = params.params

                self.symbol_table.declare(
                    name.name if isinstance(name, IdentifierNode) else name.value, 
                    Symbol(name.name, f"func<{return_type}>")
                )

                prev_type = self.current_function_type
                self.current_function_type = return_type
                self._pop(5)
                func_node = FunctionNode(return_type, name.name if isinstance(name, IdentifierNode) else name.value, param_list, block)
                self.current_function_type = prev_type

                self.stack.append(func_node)
                return True

        # ── variant D: single param already reduced to ParamNode ──────────────
        if len(self.stack) >= 5:
            dtype, recipe, name, param, block = self.stack[-5:]
            if self._is_token(dtype, type_tokens) \
               and self._is_token(recipe, TT.RECIPE) \
               and isinstance(name, IdentifierNode) \
               and isinstance(param, ParamNode) \
               and isinstance(block, BlockNode):

                return_type = self._map_type(dtype.type)

                self.symbol_table.declare(
                    name.name if isinstance(name, IdentifierNode) else name.value, 
                    Symbol(name.name, f"func<{return_type}>")
                )

                prev_type = self.current_function_type
                self.current_function_type = return_type
                self._pop(5)
                func_node = FunctionNode(return_type, name.name if isinstance(name, IdentifierNode) else name.value, [param], block)
                self.current_function_type = prev_type

                self.stack.append(func_node)
                return True

        # ── variant A: with params (old pattern, tokens not reduced) ────────────
        if len(self.stack) >= 7:
            dtype, recipe, name, lp, params, rp, block = self.stack[-7:]
            if self._is_token(dtype, type_tokens) \
               and self._is_token(recipe, TT.RECIPE) \
               and isinstance(name, IdentifierNode) \
               and self._is_token(lp, TT.LPAREN) \
               and isinstance(params, (ParamNode, ParamListNode)) \
               and self._is_token(rp, TT.RPAREN) \
               and isinstance(block, BlockNode):

                return_type = self._map_type(dtype.type)
                param_list  = params.params if isinstance(params, ParamListNode) else [params]

                # ✅ FIX 3: register function in the OUTER (currently active) scope
                self.symbol_table.declare(
                    name.name if isinstance(name, IdentifierNode) else name.value, Symbol(name.name, f"func<{return_type}>")
                )

                # ✅ FIX 4b: track return type; restore outer function's on exit
                prev_type = self.current_function_type
                self.current_function_type = return_type
                self._pop(7)
                func_node = FunctionNode(return_type, name.name if isinstance(name, IdentifierNode) else name.value, param_list, block)
                self.current_function_type = prev_type

                self.stack.append(func_node)
                return True

        # ── variant B: no params (old pattern, tokens not reduced) ─────────────
        if len(self.stack) >= 6:
            dtype, recipe, name, lp, rp, block = self.stack[-6:]
            if self._is_token(dtype, type_tokens) \
               and self._is_token(recipe, TT.RECIPE) \
               and isinstance(name, IdentifierNode) \
               and self._is_token(lp, TT.LPAREN) \
               and self._is_token(rp, TT.RPAREN) \
               and isinstance(block, BlockNode):

                return_type = self._map_type(dtype.type)

                # ✅ FIX 3
                self.symbol_table.declare(
                    name.name if isinstance(name, IdentifierNode) else name.value, Symbol(name.name if isinstance(name, IdentifierNode) else name.value, f"func<{return_type}>")
                )

                # ✅ FIX 4b
                prev_type = self.current_function_type
                self.current_function_type = return_type
                self._pop(6)
                func_node = FunctionNode(return_type, name.name if isinstance(name, IdentifierNode) else name.value , [], block)
                self.current_function_type = prev_type

                self.stack.append(func_node)
                return True
        
        return False

    # ✅ FIX 4c: validate return expression type against the enclosing function
    def _return_stmt(self):
        if len(self.stack) >= 3:
            bill, expr, semi = self.stack[-3:]
            if self._is_token(bill, TT.BILL) and isinstance(expr, Node) \
               and self._is_token(semi, TT.SEMICOLON):

                if self.current_function_type is not None:
                    if not self._check_types(expr.dtype, self.current_function_type):
                        raise Exception(
                            f"❌ Return type mismatch: "
                            f"expected '{self.current_function_type}', "
                            f"got '{expr.dtype}'"
                        )

                self._pop(3)
                self.stack.append(ReturnNode(expr))
                return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # ARRAYS
    # ─────────────────────────────────────────────────────────────────────────

    def _array_values(self):
        """
        Matches:  { Expr , Expr , ... }

        Also pops from scope_stack to stay in sync with the '{' that was shifted
        (which pushed None because an array literal is not a block context).
        """
        if len(self.stack) < 3:
            return False
        if not self._is_token(self.stack[-1], TT.LBRACE):
            return False

        values = []
        i = -2

        while i >= -len(self.stack):
            item = self.stack[i]
            if isinstance(item, Node):
                values.insert(0, item)
                i -= 1
                if i >= -len(self.stack) and self._is_token(self.stack[i], TT.COMMA):
                    i -= 1
            elif self._is_token(item, TT.RBRACE):
                num_items = abs(i) + 1

                # ✅ FIX 5: all array elements must share the same type
                if values:
                    first_type = values[0].dtype
                    for v in values:
                        if v.dtype != first_type:
                            raise Exception(
                                f"❌ Array type mismatch: "
                                f"expected '{first_type}', got '{v.dtype}'"
                            )

                # Keep scope_stack in sync (None was pushed for this '{')
                scope_type = self.scope_stack.pop() if self.scope_stack else None
                if scope_type is not None:
                    self.symbol_table.pop_scope()

                self._pop(num_items)
                self.stack.append(ArrayValuesNode(values))
                return True
            else:
                break

        return False

    def _array_decl(self):
        if len(self.stack) >= 9:
            dtype, package, name, lb, size, rb, eq, values, semi = self.stack[-9:]
            if self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) \
               and self._is_token(package, TT.PACKAGE) \
               and isinstance(name, IdentifierNode) \
               and self._is_token(lb, TT.LBRACKET) \
               and self._is_token(size, TT.NUMBER) \
               and self._is_token(rb, TT.RBRACKET) \
               and self._is_token(eq, TT.ASSIGN) \
               and isinstance(values, ArrayValuesNode) \
               and self._is_token(semi, TT.SEMICOLON):

                var_type = self._map_type(dtype.type)
                self.symbol_table.declare(name.name, Symbol(name.name, f"array<{var_type}>"))
                self._pop(9)
                self.stack.append(ArrayDeclNode(var_type, name.name, int(size.value), values))
                return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # STATEMENTS
    # ─────────────────────────────────────────────────────────────────────────

    def _var_decl(self):#تحويل:
# Type id = Expr ;
# ⬇️
# VarDeclNode + تسجيل المتغير + فحص النوع
        if len(self.stack) < 5:
            return False
        dtype, name, eq, expr, semi = self.stack[-5:]
        if self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) \
           and isinstance(name, IdentifierNode) \
           and self._is_token(eq, TT.ASSIGN) \
           and isinstance(expr, Node) \
           and self._is_token(semi, TT.SEMICOLON):
            var_type = self._map_type(dtype.type)
            self.symbol_table.declare(name.name, Symbol(name.name, var_type))
            if not self._check_types(var_type, expr.dtype):
                raise Exception(f"❌ Type mismatch in declaration of '{name.name}'")
            self._pop(5)
            self.stack.append(VarDeclNode(var_type, name.name, expr))
            return True
        return False

    def _var_decl_no_init(self):
        if len(self.stack) < 3:
            return False
        dtype, name, semi = self.stack[-3:]
        if self._is_token(dtype, [TT.COUNT, TT.NOTE, TT.COIN, TT.MEASURE, TT.EMO]) \
           and isinstance(name, IdentifierNode) \
           and self._is_token(semi, TT.SEMICOLON):
            var_type = self._map_type(dtype.type)
            self.symbol_table.declare(name.name, Symbol(name.name, var_type))
            self._pop(3)
            self.stack.append(VarDeclNode(var_type, name.name, None))
            return True
        return False

    def _assignment(self):
        if len(self.stack) < 4:
            return False
        name, eq, expr, semi = self.stack[-4:]
        if isinstance(name, IdentifierNode) \
           and self._is_token(eq, TT.ASSIGN) \
           and isinstance(expr, Node) \
           and self._is_token(semi, TT.SEMICOLON):
            symbol = self.symbol_table.lookup(name.name)
            if not self._check_types(symbol.data_type, expr.dtype):
                raise Exception(f"❌ Type mismatch in assignment to '{name.name}'")
            self._pop(4)
            self.stack.append(AssignNode(name.name, expr))
            return True
        return False

    def _print(self):
        if len(self.stack) < 4:
            return False
        serve, op, expr, semi = self.stack[-4:]
        if self._is_token(serve, TT.SERVE) \
           and self._is_token(op, TT.SHIFT_LEFT) \
           and isinstance(expr, Node) \
           and self._is_token(semi, TT.SEMICOLON):
            self._pop(4)
            self.stack.append(IOOutputNode(expr))
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _pop(self, n):
        for _ in range(n):
            self.stack.pop()

    def _peek(self):
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def _match_token(self, index, token_type):
        if len(self.stack) >= abs(index):
            item = self.stack[index]
            return hasattr(item, "type") and item.type == token_type
        return False

    def _is_token(self, obj, types):
        if not hasattr(obj, "type"):
            return False
        return obj.type in types if isinstance(types, list) else obj.type == types