from fpdf import FPDF
from pathlib import Path

sample_dir = Path(__file__).parent / "sample_docs"
sample_dir.mkdir(exist_ok=True)

class PDFDoc(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, self.doc_title, border=False, align='C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def create_college_notes():
    pdf = PDFDoc()
    pdf.doc_title = "CS301: Advanced Operating Systems - Lecture Notes"
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Unit 1: Virtual Memory & Page Replacement Algorithms", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, (
        "Virtual memory decouples the programmer's view of memory from physical reality. "
        "Each process runs in its own private 64-bit address space divided into fixed-size units called pages "
        "(typically 4 KB or 2 MB huge pages). The MMU (Memory Management Unit) translates virtual addresses "
        "to physical frame numbers using a multi-level page table structure.\n\n"
        "Key replacement policies include:\n"
        "1. Optimal Replacement (OPT): Discard the page that will not be accessed for the longest period in the future (theoretical baseline).\n"
        "2. Least Recently Used (LRU): Evict the page that has not been referenced for the longest duration. Uses timestamp or hardware reference bits.\n"
        "3. Clock / Second Chance: An approximation of LRU using a circular buffer and a use-bit.\n\n"
        "Thrashing occurs when the sum of working set sizes across all active processes exceeds physical RAM, causing constant page faults."
    ))

    # Page 2
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Unit 2: Concurrency, Mutexes, and Deadlock Prevention", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, (
        "Concurrency introduces race conditions when two or more threads attempt to manipulate shared memory concurrently.\n\n"
        "To ensure mutual exclusion, systems utilize:\n"
        "- Mutex Locks: Binary flag ensuring only one thread enters the critical section at a time.\n"
        "- Counting Semaphores: Maintained via P() [wait] and V() [signal] operations, allowing up to N concurrent threads.\n"
        "- Read-Write Locks: Permits multiple concurrent readers or a single exclusive writer.\n\n"
        "Deadlock requires four necessary conditions (Coffman Conditions):\n"
        "1. Mutual Exclusion\n"
        "2. Hold and Wait\n"
        "3. No Preemption\n"
        "4. Circular Wait\n\n"
        "Prevention: Impose a global total ordering on all locks (Lock Acquisition Hierarchy) to break circular wait."
    ))

    # Page 3
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Unit 3: Distributed Consensus & The Raft Protocol", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, (
        "Consensus in distributed systems requires multiple independent nodes to agree on state transitions despite node crashes or network partitions.\n\n"
        "The Raft consensus algorithm decomposes consensus into three subproblems:\n"
        "1. Leader Election: When a node's heartbeat timer expires without contact from the leader, it increments term number, votes for itself, and broadcasts RequestVote RPCs.\n"
        "2. Log Replication: The elected leader receives client state machine commands, appends them to its local write-ahead log, and broadcasts AppendEntries RPCs to followers.\n"
        "3. Safety Invariant: Once an entry has been committed in a given term, that entry will be present in the logs of the leaders for all higher terms.\n\n"
        "Quorum requirement: (N/2) + 1 active nodes must acknowledge an entry before it is considered committed."
    ))

    target = sample_dir / "sample_college_notes.pdf"
    pdf.output(str(target))
    print(f"Created: {target}")

def create_company_policy():
    pdf = PDFDoc()
    pdf.doc_title = "GlobalTech Inc. - Employee Policy Handbook 2026"
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Section 1: Working Hours & Hybrid Work Model", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, (
        "Welcome to GlobalTech Inc. This handbook establishes our corporate standards, entitlements, and conduct rules.\n\n"
        "1. Core Working Hours: All full-time employees are expected to be available for team collaboration between 10:00 AM and 4:00 PM in their local timezone.\n"
        "2. Hybrid Work Policy: Employees in engineering, design, and operations are entitled to work remotely up to 3 days per week. "
        "Tuesdays and Thursdays are mandatory in-office anchor days for team reviews and sprint planning.\n"
        "3. Overtime: Non-exempt personnel must receive prior written authorization from their department director before logging hours exceeding 40 hours per week."
    ))

    # Page 2
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Section 2: Paid Time Off (PTO), Sick Leave & Parental Benefits", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, (
        "1. Annual Vacation Allowance: All full-time staff receive 25 days of paid vacation per calendar year, accrued monthly at 2.08 days per month.\n"
        "2. Sick Leave: Up to 10 days of paid sick leave are provided annually. A medical certificate from a certified practitioner is required for consecutive absences lasting more than 3 business days.\n"
        "3. Parental Leave: Primary caregivers receive 16 weeks of 100% paid parental leave. Secondary caregivers receive 6 weeks of 100% paid leave. Eligible after 6 months of continuous employment.\n"
        "4. Carry-Over Limit: A maximum of 5 unused vacation days may roll over into the following calendar year, expiring on March 31st."
    ))

    # Page 3
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Section 3: Equipment Reimbursement & Data Security Compliance", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, (
        "1. Home Office Stipend: Each employee receives a one-time reimbursement of up to $1,000 USD for ergonomic desks, chairs, and monitors upon hiring.\n"
        "2. Internet & Phone Subsidy: GlobalTech provides a recurring monthly allowance of $60 USD for high-speed home broadband expenses.\n"
        "3. Device Security Requirements:\n"
        "   - All laptops must use full disk encryption (BitLocker / FileVault).\n"
        "   - Multi-Factor Authentication (MFA) is strictly mandatory on all corporate accounts.\n"
        "   - Client and proprietary code must never be uploaded to unapproved public AI tools or personal storage without written approval from the CISO."
    ))

    target = sample_dir / "sample_company_policy.pdf"
    pdf.output(str(target))
    print(f"Created: {target}")

if __name__ == "__main__":
    create_college_notes()
    create_company_policy()
