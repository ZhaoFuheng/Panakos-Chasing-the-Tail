#include<core.p4>
#if __TARGET_TOFINO__ == 2
#include<t2na.p4>
#else
#include<tna.p4>
#endif


#define COUNTMIN_T 16
#define DELTA_COUNTMIN_T 1
#define COUNTMIN_LEN 32768
#define COUNTMIN_HASH_LEN 15
#define BITMAP_LEN 131072
#define BITMAP_HASH_LEN 17
#define COUNTER_LEN 2048
#define COUNTER_HASH_LEN 11
#define DELTA_COUNT_T 1
#define PADDING 1

/* header definitions */
header Ethernet {
	bit<48> dstAddr;
	bit<48> srcAddr;
	bit<16> etherType;
}

header Ipv4{
	bit<4> version;
	bit<4> ihl;
	bit<8> diffserv;
    bit<16> total_len;
	bit<16> identification;
	bit<3> flags;
	bit<13> fragOffset;
	bit<8> ttl;
    bit<8> protocol;
	bit<16> checksum;
	bit<32> srcAddr;
	bit<32> dstAddr;
}  
header MyFlow{
	bit<32> id;
}

struct ingress_headers_t{
	Ethernet ethernet;
	Ipv4 ipv4;
	MyFlow myflow;
}


header update_digest_h{
	bit<8> type;
	bit<32> key;
	bit<8> bitmapCount;
	bit<8> countminCount1;
	bit<8> countminCount2;
	bit<32> cocoCount;
	bit<32> cocoCount2;
	bit<32> id;
	bit<32> id2;
	bit<8> delta;
	bit<BITMAP_HASH_LEN> hashval;
	bit<COUNTMIN_HASH_LEN> hashval2;
	bit<COUNTMIN_HASH_LEN> hashval3;
	bit<PADDING> padding;
}

header update_digest_countmin_h{
	bit<8> count1;
	bit<8> count2;
}
struct ingress_metadata_t{

    bit<8> bitmapCount;

	bit<8> countminCount;
	bit<8> countminCount2;
	bit<BITMAP_HASH_LEN> hashval;
	bit<COUNTMIN_HASH_LEN> hashval2;
	bit<COUNTMIN_HASH_LEN> hashval3;

	bit<32> count;
	bit<8> deltaCount;

  	bit<16> rng;
	bit<32> cond;
	bit<32> id;

	bit<32> count2;
	bit<8> deltaCount2;

  	bit<16> rng2;
	bit<32> cond2;
	bit<32> id2;

	MirrorId_t sid;
	bool send_update;
	bit<8> clone_type;
}

struct egress_headers_t {}
struct egress_metadata_t {}

enum bit<16> ether_type_t {
    IPV4    = 0x0800,
    ARP     = 0x0806
}

enum bit<8> ip_proto_t {
    ICMP    = 1,
    IGMP    = 2,
    TCP     = 6,
    UDP     = 17
}

/* parser processing */
@pa_atomic("ingress", "metadata.rng")
@pa_atomic("ingress", "metadata.cond")
parser IngressParser(packet_in pkt,
	out ingress_headers_t hdr,
	out ingress_metadata_t metadata,
	out ingress_intrinsic_metadata_t ig_intr_md)
{
	state start{
		pkt.extract(ig_intr_md);
		pkt.advance(PORT_METADATA_SIZE);
		transition parse_ethernet;
	}

	state parse_ethernet{
		pkt.extract(hdr.ethernet);
        transition select((bit<16>)hdr.ethernet.etherType) {
            (bit<16>)ether_type_t.IPV4      : parse_ipv4;
            (bit<16>)ether_type_t.ARP       : accept;
            default : accept;
        }
	}

	state parse_ipv4{
		pkt.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            (bit<8>)ip_proto_t.ICMP             : accept;
            (bit<8>)ip_proto_t.IGMP             : accept;
            (bit<8>)ip_proto_t.TCP              : parse_myflow;
            (bit<8>)ip_proto_t.UDP              : parse_myflow;
            default : accept;
        }
	}

	state parse_myflow{
		pkt.extract(hdr.myflow);
		transition accept;
	}

}


/* ingress */
control Ingress(inout ingress_headers_t hdr,
		inout ingress_metadata_t meta,
		in ingress_intrinsic_metadata_t ig_intr_md,
		in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
		inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
		inout ingress_intrinsic_metadata_for_tm_t ig_tm_md)
{

	/* Hash Functions */
	CRCPolynomial<bit<32>>(coeff=0x11EDC6F41,reversed=true, msb=false, extended=false, init=0x0000000, xor=0xFFFFFFFF) crc32c;

	CRCPolynomial<bit<32>>(coeff=0x104C11DB7,reversed=true, msb=false, extended=false, init=0x0000000, xor=0xFFFFFFFF) crc32;
	
	/* Bitmap */
	Hash<bit<BITMAP_HASH_LEN>>(HashAlgorithm_t.CUSTOM, crc32c) bitmap_hash;
	
	Register<bit<8>,bit<BITMAP_HASH_LEN>>(BITMAP_LEN) bitmap_count;

	RegisterAction<bit<8>,bit<BITMAP_HASH_LEN>,bit<8>>(bitmap_count) bitmap_count_alu={
		void apply(inout bit<8> register_data, out bit<8> alu_data){
			if (register_data < 3){

				register_data = register_data + 1;
			}
			alu_data = register_data;
		}
	};

	action check_bitmap_count(){
		meta.clone_type = 1;
		meta.hashval = bitmap_hash.get({hdr.myflow.id});
		meta.bitmapCount = bitmap_count_alu.execute(bitmap_hash.get({hdr.myflow.id}));
	}

	table bitmap_count_table{
		actions = {
			check_bitmap_count;
		}
		size = 1;
		const default_action = check_bitmap_count();
	}	

	/* Count Min */

	Hash<bit<COUNTMIN_HASH_LEN>>(HashAlgorithm_t.CUSTOM, crc32c) countmin_hash;
	
	Register<bit<8>,bit<COUNTMIN_HASH_LEN>>(COUNTMIN_LEN) countmin_count;

	RegisterAction<bit<8>,bit<COUNTMIN_HASH_LEN>,bit<8>>(countmin_count) countmin_count_alu={
		void apply(inout bit<8> register_data, out bit<8> alu_data){
			if (register_data <= COUNTMIN_T){
				register_data = register_data + 1;
			}
			alu_data = register_data;
		}
	};

	Hash<bit<COUNTMIN_HASH_LEN>>(HashAlgorithm_t.CUSTOM, crc32) countmin_hash2;
	
	Register<bit<8>,bit<COUNTMIN_HASH_LEN>>(COUNTMIN_LEN) countmin_count2;

	RegisterAction<bit<8>,bit<COUNTMIN_HASH_LEN>,bit<8>>(countmin_count2) countmin_count_alu2={
		void apply(inout bit<8> register_data, out bit<8> alu_data){
			if (register_data <= COUNTMIN_T){
				register_data = register_data + 1;
			}
			alu_data = register_data;
		}
	};
	action check_countmin_count(){
		meta.clone_type = 2;
		meta.hashval2 = countmin_hash.get({hdr.myflow.id});
		meta.countminCount = countmin_count_alu.execute(countmin_hash.get({hdr.myflow.id}));
	}

	table countmin_count_table{
		actions = {
			check_countmin_count;
		}
		size = 1;
		const default_action = check_countmin_count();
	}	
	action check_countmin_count2(){
		meta.hashval3 = countmin_hash2.get({hdr.myflow.id});
		meta.countminCount2 = countmin_count_alu2.execute(countmin_hash2.get({hdr.myflow.id}));
	}

	table countmin_count_table2{
		actions = {
			check_countmin_count2;
		}
		size = 1;
		const default_action = check_countmin_count2();
	}	


	/* CocoSketch */
	

	/* First d */

	Hash<bit<COUNTER_HASH_LEN>>(HashAlgorithm_t.CUSTOM, crc32) counter_hash;
	
	Register<bit<32>,bit<COUNTER_HASH_LEN>>(COUNTER_LEN) counter_count;

	RegisterAction<bit<32>,bit<COUNTER_HASH_LEN>,bit<32>>(counter_count) counter_count_alu={
		void apply(inout bit<32> register_data, out bit<32> alu_data){
			register_data = register_data + 1;
			alu_data = register_data;
		}
	};

	action check_counter_count(){
		meta.clone_type = 3;
		meta.count = counter_count_alu.execute(counter_hash.get({hdr.myflow.id}));
	}

	table counter_count_table{
		actions = {
			check_counter_count;
		}
		size = 1;
		const default_action = check_counter_count();
	}	

	Register<bit<8>,bit<COUNTER_HASH_LEN>>(COUNTER_LEN) counter_delta_count;

	RegisterAction<bit<8>,bit<COUNTER_HASH_LEN>,bit<8>>(counter_delta_count) counter_delta_count_alu={
		void apply(inout bit<8> register_data, out bit<8> alu_data){
			if(register_data < DELTA_COUNT_T){
				register_data = register_data + 1;
			}
			else {
				register_data = 1;
			}
			alu_data = register_data;
		}
	};
	
	RegisterAction<bit<32>,bit<COUNTER_HASH_LEN>,bit<32>>(counter_delta_count) counter_delta_reset_alu={
		void apply(inout bit<32> register_data){
			register_data = 1;
		}
	};


	action check_delta_counter_count(){
		
		meta.deltaCount = counter_delta_count_alu.execute(counter_hash.get({hdr.myflow.id}));
	}



	table counter_delta_count_table{
		actions = {
			check_delta_counter_count;
		}
		size = 1;
		const default_action = check_delta_counter_count();
	}

	Random<bit<16>>() random_generator;

	action generate_random_number(){
		meta.rng = random_generator.get();
	}

	table random_number_table{
		actions = {
			generate_random_number;
		}
		size = 1;
		const default_action = generate_random_number();
	}

	Register<bit<32>,bit<1>>(1) num_32;

	MathUnit<bit<32>>(true,0,9,{68,73,78,85,93,102,113,128,0,0,0,0,0,0,0,0}) prog_64K_div_mu;

	RegisterAction<bit<32>,bit<1>,bit<32>>(num_32) prog_64K_div_x = {
		void apply(inout bit<32> register_data, out bit<32> mau_value){
			register_data = prog_64K_div_mu.execute(meta.count);
            mau_value = register_data;
		}
	};
	
	action calc_cond_pre(){
		meta.cond = prog_64K_div_x.execute(0);
	}

	table calc_cond_table_pre{
		actions = {
			calc_cond_pre;
		}
		size = 1;
		const default_action = calc_cond_pre();
	}
	 
	action calc_cond(){
		meta.cond = (bit<32>)meta.rng - meta.cond;
	}

	table calc_cond_table{
		actions = {
			calc_cond;
		}
		size = 1;
		const default_action = calc_cond();
	}

	Register<bit<32>,bit<COUNTER_HASH_LEN>>(COUNTER_LEN) counter_ID;

	RegisterAction<bit<32>,bit<COUNTER_HASH_LEN>,bit<32>>(counter_ID) counter_ID_alu = {
		void apply(inout bit<32> register_data, out bit<32> alu_data){
			if(register_data == 0 || meta.cond < 65536){
				register_data = hdr.myflow.id;
			}

			alu_data = register_data;
		}
	};

	action check_counter_ID(){
		meta.id = counter_ID_alu.execute(counter_hash.get({hdr.myflow.id}));
	}

	table counter_ID_table{
		actions = {
			check_counter_ID;
		}
		size = 1;
		const default_action = check_counter_ID();
	}

	/* second d */

	Hash<bit<COUNTER_HASH_LEN>>(HashAlgorithm_t.CUSTOM, crc32c) counter_hash2;
	
	Register<bit<32>,bit<COUNTER_HASH_LEN>>(COUNTER_LEN) counter_count2;

	RegisterAction<bit<32>,bit<COUNTER_HASH_LEN>,bit<32>>(counter_count2) counter_count_alu2={
		void apply(inout bit<32> register_data, out bit<32> alu_data){
			register_data = register_data + 1;
			alu_data = register_data;
		}
	};

	action check_counter_count2(){
		meta.clone_type = 3;
		meta.count2 = counter_count_alu2.execute(counter_hash2.get({hdr.myflow.id}));
	}

	table counter_count_table2{
		actions = {
			check_counter_count2;
		}
		size = 1;
		const default_action = check_counter_count2();
	}	

	Register<bit<8>,bit<COUNTER_HASH_LEN>>(COUNTER_LEN) counter_delta_count2;

	RegisterAction<bit<8>,bit<COUNTER_HASH_LEN>,bit<8>>(counter_delta_count2) counter_delta_count_alu2={
		void apply(inout bit<8> register_data, out bit<8> alu_data){
			if(register_data < DELTA_COUNT_T){
				register_data = register_data + 1;
			}
			else {
				register_data = 1;
			}
			alu_data = register_data;
		}
	};
	
	RegisterAction<bit<32>,bit<COUNTER_HASH_LEN>,bit<32>>(counter_delta_count2) counter_delta_reset_alu2={
		void apply(inout bit<32> register_data){
			register_data = 1;
		}
	};


	action check_delta_counter_count2(){
		
		meta.deltaCount2 = counter_delta_count_alu2.execute(counter_hash2.get({hdr.myflow.id}));
	}



	table counter_delta_count_table2{
		actions = {
			check_delta_counter_count2;
		}
		size = 1;
		const default_action = check_delta_counter_count2();
	}

	Random<bit<16>>() random_generator2;

	action generate_random_number2(){
		meta.rng2 = random_generator2.get();
	}

	table random_number_table2{
		actions = {
			generate_random_number2;
		}
		size = 1;
		const default_action = generate_random_number2();
	}

	Register<bit<32>,bit<1>>(1) num_32_2;

	MathUnit<bit<32>>(true,0,9,{68,73,78,85,93,102,113,128,0,0,0,0,0,0,0,0}) prog_64K_div_mu2;

	RegisterAction<bit<32>,bit<1>,bit<32>>(num_32_2) prog_64K_div_x2 = {
		void apply(inout bit<32> register_data, out bit<32> mau_value){
			register_data = prog_64K_div_mu2.execute(meta.count2);
            mau_value = register_data;
		}
	};
	
	action calc_cond_pre2(){
		meta.cond2 = prog_64K_div_x2.execute(0);
	}

	table calc_cond_table_pre2{
		actions = {
			calc_cond_pre2;
		}
		size = 1;
		const default_action = calc_cond_pre2();
	}
	 
	action calc_cond2(){
		meta.cond2 = (bit<32>)meta.rng2 - meta.cond2;
	}

	table calc_cond_table2{
		actions = {
			calc_cond2;
		}
		size = 1;
		const default_action = calc_cond2();
	}

	Register<bit<32>,bit<COUNTER_HASH_LEN>>(COUNTER_LEN) counter_ID2;

	RegisterAction<bit<32>,bit<COUNTER_HASH_LEN>,bit<32>>(counter_ID2) counter_ID_alu2 = {
		void apply(inout bit<32> register_data, out bit<32> alu_data){
			if(register_data == 0 || meta.cond2 < 65536){
				register_data = hdr.myflow.id;
			}

			alu_data = register_data;
		}
	};

	action check_counter_ID2(){
		meta.id2 = counter_ID_alu2.execute(counter_hash2.get({hdr.myflow.id}));
	}

	table counter_ID_table2{
		actions = {
			check_counter_ID2;
		}
		size = 1;
		const default_action = check_counter_ID2();
	}


	action send_update(){
		ig_dprsr_md.mirror_type = 1;
		meta.sid = 241;
	}

	table send_update_table{
		actions = {
			send_update;
		}
		size = 1;
		const default_action = send_update();
	}

	action send_update_countmin(){
		ig_dprsr_md.mirror_type = 1;
		meta.sid = 241;
	}

	table send_update_countmin_table{
		actions = {
			send_update_countmin;
		}
		size = 1;
		const default_action = send_update_countmin();
	}

	action send_update_bitmap(){
		ig_dprsr_md.mirror_type = 1;
		meta.sid = 241;
	}

	table send_update_bitmap_table{
		actions = {
			send_update_bitmap;
		}
		size = 1;
		const default_action = send_update_bitmap();
	}

	/* ingress processing*/
	apply{
        if ( hdr.myflow.isValid()) {
			bitmap_count_table.apply();
			if (meta.bitmapCount > 2){
				countmin_count_table.apply();
				countmin_count_table2.apply();
				if(meta.countminCount > COUNTMIN_T){
					if(meta.countminCount2 > COUNTMIN_T){
						counter_count_table.apply();
						counter_count_table2.apply();
						
						counter_delta_count_table.apply();
						counter_delta_count_table2.apply();
						
						random_number_table.apply();
						random_number_table2.apply();
						
						calc_cond_table_pre.apply();
						calc_cond_table_pre2.apply();
						
						calc_cond_table.apply();
						calc_cond_table2.apply();
						
						counter_ID_table.apply();
						counter_ID_table2.apply();
						if(meta.deltaCount >= DELTA_COUNT_T){
							if(meta.deltaCount2 >= DELTA_COUNT_T){
								send_update_table.apply();
							}
						}
					}

				}
				if(meta.clone_type == 2){
					if(meta.countminCount > DELTA_COUNTMIN_T){
						if(meta.countminCount2 > DELTA_COUNTMIN_T){
							send_update_countmin_table.apply();
						}
					}
				}
				
			}
			if(meta.clone_type == 1){
				send_update_bitmap_table.apply();
			}
        	}
	}
}

control IngressDeparser(packet_out pkt,
	inout ingress_headers_t hdr,
	in ingress_metadata_t meta,
	in ingress_intrinsic_metadata_for_deparser_t ig_dprtr_md)
{
	Mirror() mirror;
	apply{
		if (ig_dprtr_md.mirror_type == 1){
			mirror.emit<update_digest_h>(meta.sid, { meta.clone_type, hdr.myflow.id, meta.bitmapCount, meta.countminCount, meta.countminCount2, meta.count, meta.count2, meta.id, meta.id2, meta.deltaCount, meta.hashval, meta.hashval2, meta.hashval3, 0 });
		}
		pkt.emit(hdr);
	}
}


/* egress */
parser EgressParser(packet_in pkt,
	out egress_headers_t hdr,
	out egress_metadata_t meta,
	out egress_intrinsic_metadata_t eg_intr_md)
{
	state start{
		pkt.extract(eg_intr_md);
		transition accept;
	}
}

control Egress(inout egress_headers_t hdr,
	inout egress_metadata_t meta,
	in egress_intrinsic_metadata_t eg_intr_md,
	in egress_intrinsic_metadata_from_parser_t eg_prsr_md,
	inout egress_intrinsic_metadata_for_deparser_t eg_dprsr_md,
	inout egress_intrinsic_metadata_for_output_port_t eg_oport_md)
{
	apply{}
}

control EgressDeparser(packet_out pkt,
	inout egress_headers_t hdr,
	in egress_metadata_t meta,
	in egress_intrinsic_metadata_for_deparser_t eg_dprsr_md)
{
	apply{
		pkt.emit(hdr);
	}
}


/* main */
Pipeline(IngressParser(),Ingress(),IngressDeparser(),
EgressParser(),Egress(),EgressDeparser()) pipe;

Switch(pipe) main;
